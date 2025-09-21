Questo plugin aggiunge al Cheshire Cat un **analizzatore di normative** che:

* pulisce i documenti prima dello split,
* elabora i chunk a gruppi,
* estrae righe JSON,
* fa **de-dup** in tempo reale,
* crea un **Excel formattato** scaricabile,
* e sostituisce i chunk con il JSON “pretty” della risposta del modello.

L’attivazione del plugin è **per-utente e per-tool**, controllata dal file `cat/static/tools_status.json` (fallback: disattivato).

---

## File principali

* `standard_analysis_bot.py` (questo plugin)
* Dipendenze locali (che devi avere nel tuo plugin):

  * `prompt_helper.py` → esporta `PROMPT_STD_ANALYSIS`
  * `helpers.py` → esporta
    `_clean_cid_and_control_chars`, `_extract_json_object`,
    `normalize_rows_and_write_excel`, `split_text_into_n_parts`

---

## Come funziona (flow)

### 1) `before_rabbithole_splits_text(docs, cat)`

* **Gate ON/OFF** in base a `tools_status.json` (per utente).
* Se disabilitato → ritorna `docs` invariati.
* Se abilitato → pulisce i contenuti con `_clean_cid_and_control_chars` e filtra i vuoti.

### 2) `after_rabbithole_splitted_text(chunks, cat)`

* **Gate ON/OFF** in base a `tools_status.json` (per utente).
* Se disabilitato → ritorna `chunks` invariati.
* Se abilitato:

  * elabora i chunk **a gruppi non sovrapposti da 3** (`chunk_number = 3`);

  * builda un prompt dinamico: `PROMPT_STD_ANALYSIS` + **ultima riga valida** prodotta in precedenza;

  * chiama `cat.llm(...)`, estrae l’oggetto con `_extract_json_object`;

  * **accumula** le righe con **deduplicazione** su chiave:

    ```
    ( "Chapter/Paragraph  No.",
      "Requirement/Standard Description",
      "Regulatory References" )
    ```

  * sostituisce i chunk del gruppo con un JSON “pretty” delle righe del gruppo;

  * al termine salva un **Excel** in `cat/static/<user>_requirements_<timestamp>.xlsx`
    con le colonne:

    **REQUIRED**

    * Chapter/Paragraph  No.
    * Chapter/Paragraph Title
    * Requirement/Standard Description
    * Required Data / Configuration
    * Regulatory References

    **EXTRA (vuote ma utili a lavorare)**

    * Attached Documentation
    * Value / Design Choice
    * Designer Notes
    * Risk Assessment
    * Mitigation Measures
    * Compliant (YES/NO)

  * invia sul WS un link: `Excel file created: Download`.

Se il modello restituisce testo non JSON, il gruppo viene comunque “spezzato” e re-inserito nei chunk (così non perdi contenuto) e sul WS compare un avviso.

---

## Abilitazione per utente

Il plugin controlla `cat/static/tools_status.json`.
**Attenzione:** nel sorgente ci sono due riferimenti al nome del tool; usa **sempre lo stesso**:

```python
# Consigliato: definisci in alto una costante e usala in entrambi gli hook
TOOL_KEY = "standard_analysis_bot"  # oppure "Analizzatore normative", ma sii coerente
```

E nel codice:

```python
tool_key = TOOL_KEY  # in *entrambi* gli hook
```

### Struttura minima di `tools_status.json`

```json
{
  "tools": {
    "standard_analysis_bot": {
      "user_id_tool_status": {
        "admin": true,
        "elio": true
      }
    }
  }
}
```

* Se `user_id_tool_status.<user>` è `true` → tool attivo per quell’utente.
* Se la chiave non esiste → **fallback = false** (disattivo).

Puoi gestire il file anche via gli endpoint `/tools-status` che hai già creato.

---

## Requisiti

* **Python**: richiede `pandas`.
* Scrittura su `cat/static` (il plugin crea la cartella se manca).
* Le funzioni di supporto in `helpers.py` e `prompt_helper.py`.

Installazione rapida:

```bash
pip install pandas
```

---

## Dove finiscono i file

* Excel: `cat/static/<username>_requirements_<YYYYMMDD_HHMMSS>.xlsx`
* Link di download generato con `get_static_url()` e notificato via WS.

---

## Personalizzazioni rapide

* **Nome tool**: imposta `TOOL_KEY` in cima al file e usalo in entrambi gli hook.
* **Dimensione del gruppo**: cambia `chunk_number = 3`.
* **Colonne Excel**: modifica le liste `REQUIRED_KEYS`, `EXTRA_EMPTY_COLUMNS`, `FINAL_COLUMNS`.
* **Regola di dedup**: cambia la tupla `key = (...)` nel loop di accumulo.
* **Pulizia contenuti**: sostituisci/estendi `_clean_cid_and_control_chars`.

---

## Messaggi e logging

* Il plugin usa `cat.send_ws_message(..., "chat")` per:

  * notificare errori di parsing JSON per gruppi,
  * mostrare avanzamento (`📥 Elaborati chunks N-M...`),
  * pubblicare il link di download dell’Excel.

---

## Troubleshooting

* **Non parte?**
  Verifica che `tools_status.json` esista e che `user_id_tool_status.<user>` sia `true`.
* **Excel non creato**
  Il WS dirà “Nessuna riga prodotta…”: probabilmente il modello non ha restituito righe valide.
* **Errore JSON**
  Controlla `_extract_json_object` (atteso un oggetto con `rows: [...]` o una singola riga).
* **Permessi**
  Assicurati che il processo possa scrivere in `cat/static/`.
* **Incoerenza nome tool**
  Se in `before_...` usi “Analizzatore normative” e in `after_...` “standard\_analysis\_bot”, il gate potrebbe fallire. Allinea entrambi.

---

## Esempio completo di attivazione

```json
{
  "tools": {
    "standard_analysis_bot": {
      "user_id_tool_status": {
        "elio": true
      }
    }
  }
}
```

Carica alcuni documenti → il plugin pulisce, analizza, deduplica e crea l’Excel con le colonne previste.

---

## Sicurezza & fallback

* Se il file di stato non è leggibile → si assume **disattivato**.
* Se l’estrazione JSON fallisce → nessun crash: i chunk restano con il testo “grezzo”.
* Nessuna modifica allo stato dei tool viene fatta dal plugin: legge soltanto.

---

## Manutenzione

* Tieni sincronizzati i nomi chiave (costante `TOOL_KEY`).
* Aggiorna `helpers.py`/`prompt_helper.py` se cambi formato del JSON atteso.
* Se vuoi gestire impostazioni per-utente dei tool, fai riferimento al tuo schema esteso `tools_status.json` e agli endpoint `/tools-status` già presenti nel progetto.


