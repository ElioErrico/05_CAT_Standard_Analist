#tools_status_endpoint.py

from cat.mad_hatter.decorators import endpoint
from fastapi import HTTPException
import json
import os

# Percorsi (coerenti con gli altri endpoint)
try:
    root_dir = os.environ.get("CCAT_ROOT", os.getcwd())
    static_dir = os.path.join(root_dir, "cat/static/")
    tools_status_path = os.path.join(static_dir, "tools_status.json")
except Exception as e:
    print(f"Errore nel calcolo dei percorsi: {str(e)}")
    raise

# GET tools_status.json
@endpoint.get("/tools-status")
def get_tools_status():
    try:
        with open(tools_status_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File tools_status.json non trovato")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"JSON non valido: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# POST tools_status.json (sovrascrive l'intero file)
@endpoint.post("/tools-status")
def update_tools_status(new_tools_status: dict):
    try:
        # assicura che la cartella esista
        os.makedirs(static_dir, exist_ok=True)
        with open(tools_status_path, "w", encoding="utf-8") as f:
            json.dump(new_tools_status, f, indent=4, ensure_ascii=False)
        return {"status": "success", "message": "tools_status.json aggiornato con successo"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
