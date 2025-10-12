from pydantic import BaseModel
from cat.mad_hatter.decorators import plugin
from pydantic import BaseModel, Field, field_validator


class MySettings(BaseModel):
    tool_name: str = "Analizzatore normative"

@plugin
def settings_model():
    """
    Restituisce il modello Pydantic delle impostazioni.
    Il framework usa questo per validare e salvare i settings.
    """
    return MySettings