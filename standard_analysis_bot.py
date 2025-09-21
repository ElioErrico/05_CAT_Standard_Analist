# standard_analysis_bot.py

from cat.mad_hatter.decorators import hook
from cat.utils import get_static_url

import os
import json
import pandas as pd
from datetime import datetime

from .prompt_helper import PROMPT_STD_ANALYSIS
from .helpers import _clean_cid_and_control_chars, _extract_json_object
from .helpers import normalize_rows_and_write_excel
from .helpers import split_text_into_n_parts

def _format_last_row_section(last_row: dict | None) -> str:
    """
    Restituisce la stringa da appendere al PROMPT_STD_ANALYSIS
    con l'ultima riga generata, se presente.
    Il template del prompt già contiene:
      ## Ultima riga generata:
      L'ultima riga che hai inserito è:
    quindi qui aggiungiamo solo il JSON della riga.
    """
    if not last_row:
        return ""
    try:
        return "\n" + json.dumps(last_row, ensure_ascii=False) + "\n"
    except Exception:
        return "\n" + str(last_row) + "\n"


@hook  # default priority = 1
def before_rabbithole_splits_text(docs, cat):
    # ---- Guard: abilita/disabilita tool per utente; fallback=False ----
    try:
        with open("cat/static/tools_status.json", "r", encoding="utf-8") as f:
            ts = json.load(f) or {}
    except Exception:
        ts = {}

    uid = str(getattr(cat, "user_id", "") or "")
    tool_key = "Analizzatore normative"
    enabled = bool(
        ts.get("tools", {})
          .get(tool_key, {})
          .get("user_id_tool_status", {})
          .get(uid, False)
    )
    if not enabled:
        return docs


    cleaned_docs = []
    for doc in docs:
        cleaned_content = _clean_cid_and_control_chars(doc.page_content or "")
        if cleaned_content.strip():
            doc.page_content = cleaned_content
            cleaned_docs.append(doc)
    return cleaned_docs


@hook  # default priority = 1
def after_rabbithole_splitted_text(chunks, cat):
    """
    - Estrae righe JSON dai chunk a gruppi non sovrapposti
    - De-duplica le righe già durante l'accumulo
    - Scrive Excel formattato
    - Sostituisce i chunk con il JSON pretty corrispondente
    """
    
    # ---- Guard: abilita/disabilita tool per utente; fallback=False ----
    try:
        with open("cat/static/tools_status.json", "r", encoding="utf-8") as f:
            ts = json.load(f) or {}
    except Exception:
        ts = {}

    uid = str(getattr(cat, "user_id", "") or "")
    tool_key = "standard_analysis_bot"
    enabled = bool(
        ts.get("tools", {})
          .get(tool_key, {})
          .get("user_id_tool_status", {})
          .get(uid, False)
    )
    if not enabled:
        return chunks

    # --- Config colonne ---
    REQUIRED_KEYS = [
        "Chapter/Paragraph  No.",
        "Chapter/Paragraph Title",
        "Requirement/Standard Description",
        "Required Data / Configuration",
        "Regulatory References",
    ]
    EXTRA_EMPTY_COLUMNS = [
        "Attached Documentation",
        "Value / Design Choice",
        "Designer Notes",
        "Risk Assessment",
        "Mitigation Measures",
        "Compliant (YES/NO)",
    ]
    FINAL_COLUMNS = REQUIRED_KEYS + EXTRA_EMPTY_COLUMNS

    # --- Naming & path ---
    username = getattr(cat, "user_id", None) or "user"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{username}_requirements_{timestamp}.xlsx"
    static_dir = "cat/static"
    os.makedirs(static_dir, exist_ok=True)
    file_path = os.path.join(static_dir, filename)

    # Accumulatore + set per dedup in tempo reale
    all_rows = []
    seen_keys = set()  # dedup su (No., Description, References)

    # Memoria locale dell'ultima riga accettata (per il prompt del gruppo successivo)
    last_row_for_prompt: dict | None = None

    # Gruppi non sovrapposti da 3
    chunk_number = 3

    for i in range(0, len(chunks), chunk_number):
        group = chunks[i:i + chunk_number]
        concatenated_content = "\n".join([c.page_content for c in group])

        # Prompt dinamico: aggiunge l'ultima riga generata (se esiste)
        dynamic_prompt = PROMPT_STD_ANALYSIS + _format_last_row_section(last_row_for_prompt)

        # Puoi lasciare cat.llm o passare a cat.run come da discussione precedente
        response = cat.llm(dynamic_prompt + concatenated_content)

        try:
            obj = _extract_json_object(response)
        except Exception as e:
            start_idx, end_idx = i + 1, min(i + chunk_number, len(chunks))
            cat.send_ws_message(f"⚠️ Errore JSON nei chunks {start_idx}-{end_idx}: {e}", "chat")
            # Scrive comunque la risposta raw nei chunk per non perdere info
            parts = split_text_into_n_parts(str(response), len(group))
            for j, c in enumerate(group):
                c.page_content = parts[j]
            continue

        # ---- Accumulo UNA SOLA VOLTA con dedup in tempo reale ----
        rows = obj.get("rows")
        group_rows = rows if isinstance(rows, list) else [obj]
        for r in group_rows:
            key = (
                (r.get("Chapter/Paragraph  No.", "") or "").strip(),
                (r.get("Requirement/Standard Description", "") or "").strip(),
                (r.get("Regulatory References", "") or "").strip(),
            )
            if key in seen_keys:
                continue
            seen_keys.add(key)
            all_rows.append(r)
            # aggiorna l'ultima riga accettata: sarà usata nel prompt del prossimo gruppo
            last_row_for_prompt = r

        # Sostituisci i chunk del gruppo con JSON pretty della risposta (una sola volta)
        pretty_json = json.dumps({"rows": group_rows}, ensure_ascii=False, indent=2)
        parts = split_text_into_n_parts(pretty_json, len(group))
        for j, c in enumerate(group):
            c.page_content = parts[j]

        # Log avanzamento
        start_idx, end_idx = i + 1, min(i + chunk_number, len(chunks))
        cat.send_ws_message(
            f"📥 Elaborati chunks {start_idx}-{end_idx} di {len(chunks)}. Righe uniche finora: {len(all_rows)}.",
            "chat"
        )

    # --- Serializza/Deserializza (stabilizzazione) ---
    accumulated_dict = {"rows": all_rows}
    accumulated_str = json.dumps(accumulated_dict, ensure_ascii=False)
    final_dict = json.loads(accumulated_str)

    # --- Export Excel (con ulteriore dedup a livello DataFrame, per sicurezza) ---
    rows = final_dict.get("rows", [])
    if rows:
        _ = normalize_rows_and_write_excel(
            rows=rows,
            required_keys=REQUIRED_KEYS,
            extra_empty_columns=EXTRA_EMPTY_COLUMNS,
            final_columns=FINAL_COLUMNS,
            file_path=file_path,
        )
        download_url = f'{get_static_url()}{filename}?v={timestamp}'
        cat.send_ws_message(f'Excel file created: <a href="{download_url}">Download</a>', "chat")
    else:
        cat.send_ws_message("Nessuna riga prodotta: impossibile creare l’Excel.", "chat")

    return chunks
