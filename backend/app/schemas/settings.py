"""Settings schemas.

NOTE: ``GET /settings`` returns provider settings (including API keys) in plain
text; masking them is a separate, wire-changing step (audit §3.2).
"""

import json
from typing import Any, Optional

from pydantic import BaseModel

from app.db.models import Settings
from app.schemas.common import RequestModel


def _decode(value: str | None) -> Any:
    return json.loads(value) if value else {}


class SettingsOut(BaseModel):
    id: str | None
    selected_tts_provider: str | None
    selected_llm_provider: str | None
    selected_diffusion_provider: str | None
    tts_provider_settings: Any
    diffusion_provider_settings: Any
    llm_provider_settings: Any
    selected_script_generation_template: str | None
    script_generation_templates: Any

    @classmethod
    def from_model(cls, settings: Settings) -> "SettingsOut":
        return cls(
            id=settings.id,
            selected_tts_provider=settings.selected_tts_provider,
            selected_llm_provider=settings.selected_llm_provider,
            selected_diffusion_provider=settings.selected_diffusion_provider,
            tts_provider_settings=_decode(settings.tts_provider_settings),
            diffusion_provider_settings=_decode(settings.diffusion_provider_settings),
            llm_provider_settings=_decode(settings.llm_provider_settings),
            selected_script_generation_template=settings.selected_script_generation_template,
            script_generation_templates=_decode(settings.script_generation_templates),
        )


class UpdateSettingsIn(RequestModel):
    """Every field is optional; see ``settings_service.update_settings`` for merge rules."""

    selected_tts_provider: Optional[str] = None
    selected_diffusion_provider: Optional[str] = None
    selected_llm_provider: Optional[str] = None
    tts_provider_settings: Optional[dict] = None
    diffusion_provider_settings: Optional[dict] = None
    llm_provider_settings: Optional[dict] = None
    selected_script_generation_template: Optional[str] = None
    script_generation_templates: Optional[dict] = None
