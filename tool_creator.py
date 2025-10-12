# cat/plugins/tools_status/save_settings.py
from cat.mad_hatter.decorators import plugin
from typing import Any, Dict
import os
import json
import inspect, json

def _compute_path() -> str:
    root_dir = os.environ.get("CCAT_ROOT", os.getcwd())
    static_dir = os.path.join(root_dir, "cat", "static")
    os.makedirs(static_dir, exist_ok=True)
    return os.path.join(static_dir, "tools_status.json")


def _load_json(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f) or {}
            if not isinstance(data, dict):
                data = {}
    except FileNotFoundError:
        data = {}
    except Exception:
        data = {}

    data.setdefault("tools", {})
    return data


def _save_json(path: str, data: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


@plugin
def save_settings(settings: Any) -> Dict[str, Any]:
    """
    Inizializza un tool nel file tools_status.json prendendo SOLO il tool_name.

    Input accettati:
      - "Analizzatore normative"              # stringa semplice
      - {"tool_name": "Analizzatore normative"}  # dizionario

    Effetti:
      - Crea (se assente) data["tools"][tool_name] = {}.
      - NON modifica user_id_tool_status, NON aggiunge setting.
    """
    # Normalizza l'input in un tool_name
    tool_name = None
    if isinstance(settings, str):
        tool_name = settings
    elif isinstance(settings, dict):
        tool_name = settings.get("tool_name")

    if not isinstance(tool_name, str) or not tool_name.strip():
        return {"status": "error", "message": "tool_name mancante o non valido"}

    tool_name = tool_name.strip()

    path = _compute_path()
    data = _load_json(path)

    existed = tool_name in data["tools"]
    # Se esiste ma non è un dict, rimpiazza con dict vuoto
    if not existed or not isinstance(data["tools"].get(tool_name), dict):
        data["tools"][tool_name] = {}

    _save_json(path, data)

    """
    Salva i settings nel file settings.json
    """
    current_file = inspect.getfile(inspect.currentframe())
    plugin_dir = os.path.dirname(os.path.abspath(current_file))
    settings_file_path = os.path.join(plugin_dir, "settings.json")
    
    # Carica vecchi settings e unisci con i nuovi
    old_settings = {}
    if os.path.isfile(settings_file_path):
        with open(settings_file_path, "r") as f:
            old_settings = json.load(f)
    
    updated_settings = {**old_settings, **settings}
    
    # Salva
    with open(settings_file_path, "w") as f:
        json.dump(updated_settings, f, indent=4)
    
    return updated_settings