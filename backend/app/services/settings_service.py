"""Settings use-cases: read, provider-settings merge on update, and a snapshot
for the AI provider classes."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Settings
from app.db.session import async_session_maker
from app.repositories import settings as settings_repo
from app.schemas.settings import SettingsOut, UpdateSettingsIn


async def get_settings(session: AsyncSession) -> Settings | None:
    return await settings_repo.get(session)


async def get_settings_dict() -> dict[str, Any] | None:
    """Serialized settings read in a session of its own (``None`` if no row exists).

    Used by the AI provider classes (``app/ai``) and the script generator, which
    look up their provider configuration themselves.
    """
    async with async_session_maker() as session:
        settings = await settings_repo.get(session)
        return SettingsOut.from_model(settings).model_dump() if settings else None


def _merge_changes(current: SettingsOut | None, update: UpdateSettingsIn) -> dict[str, Any]:
    """Column values to write for ``update`` on top of ``current``.

    * ``script_generation_templates`` is merged key by key; a ``None`` value deletes
      the template.
    * Selecting a provider stores that provider's settings under its name in the
      provider-settings dict (``None`` when none are sent), keeping the others.
    """
    changes: dict[str, Any] = {}

    if update.selected_script_generation_template is not None:
        changes["selected_script_generation_template"] = update.selected_script_generation_template

    if update.script_generation_templates is not None:
        templates = dict(current.script_generation_templates) if current and current.script_generation_templates else {}
        for key, value in update.script_generation_templates.items():
            if value is None:
                templates.pop(key, None)
            else:
                templates[key] = value
        changes["script_generation_templates"] = templates

    for kind in ("tts", "diffusion", "llm"):
        provider = getattr(update, f"selected_{kind}_provider")
        if provider is None:
            continue
        settings_field = f"{kind}_provider_settings"
        previous = getattr(current, settings_field) if current and getattr(current, settings_field) else {}
        changes[f"selected_{kind}_provider"] = provider
        changes[settings_field] = {**previous, provider: getattr(update, settings_field)}

    return changes


async def update_settings(session: AsyncSession, update: UpdateSettingsIn) -> dict[str, Any] | SettingsOut:
    """Create or update the settings row; returns the ``"settings"`` response value.

    Wire compatibility: creating returns the serialized row *before* the INSERT
    (so ``id`` is ``None``); updating returns ``{"message": ...}`` (audit B15).
    """
    settings = await settings_repo.get(session)
    changes = _merge_changes(SettingsOut.from_model(settings) if settings else None, update)

    if settings is None:
        result: dict[str, Any] | SettingsOut = SettingsOut.from_model(settings_repo.add(session, **changes))
    else:
        settings_repo.apply(settings, **changes)
        result = {"message": "Settings updated successfully"}

    await session.commit()
    return result
