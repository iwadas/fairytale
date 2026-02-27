from fastapi import APIRouter, Body, HTTPException

from database.crud import get_settings_db, update_settings_db, create_settings_db
from typing import Optional


router = APIRouter(prefix="/settings", tags=["settings"])

@router.get("")
async def get_settings():   
    settings = await get_settings_db()
    return settings


@router.put("")
async def update_settings(
    selected_tts_provider: Optional[str] = Body(None, embed=True),
    selected_diffusion_provider: Optional[str] = Body(None, embed=True),
    selected_llm_provider: Optional[str] = Body(None, embed=True),
    tts_provider_settings: Optional[dict] = Body(None, embed=True),
    diffusion_provider_settings: Optional[dict] = Body(None, embed=True),
    llm_provider_settings: Optional[dict] = Body(None, embed=True),
):

    settings = await get_settings_db()
    
    kwargs = {}



    if selected_tts_provider is not None:
        kwargs["selected_tts_provider"] = selected_tts_provider
        previous_provider_settings = settings["tts_provider_settings"] if settings and settings.get("tts_provider_settings") else {}
        kwargs["tts_provider_settings"] = {selected_tts_provider: tts_provider_settings} 
    
    if selected_diffusion_provider is not None:
        kwargs["selected_diffusion_provider"] = selected_diffusion_provider
        previous_provider_settings = settings["diffusion_provider_settings"] if settings and settings.get("diffusion_provider_settings") else {}
        kwargs["diffusion_provider_settings"] = {**previous_provider_settings, selected_diffusion_provider: diffusion_provider_settings}
    
    if selected_llm_provider is not None:
        kwargs["selected_llm_provider"] = selected_llm_provider
        previous_provider_settings = settings["llm_provider_settings"] if settings and settings.get("llm_provider_settings") else {}
        kwargs["llm_provider_settings"] = {**previous_provider_settings, selected_llm_provider: llm_provider_settings}

        
    if not settings:
        updated_settings = await create_settings_db(**kwargs)
    else:
        updated_settings = await update_settings_db(**kwargs)

    return {"message": "Settings updated successfully", "settings": updated_settings}
   