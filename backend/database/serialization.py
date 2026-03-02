from database.models import (
    Project, 
    Character,
    Place, 
    Scene,
    Settings, 
    Voiceover, 
    ImagesPackage, 
    PhotoDumpImage, 
    SceneImage, 
    Music
)
import json
from sqlalchemy import inspect

def is_loaded(obj, attr_name):
    """Helper to check if a relationship is loaded to avoid async errors."""
    ins = inspect(obj)
    return attr_name not in ins.unloaded

def serialize_project(project: Project):
    return {
        "id": project.id,
        "name": project.name,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "type": project.type,
        # Now these are safe too:
        "characters": [serialize_character(c) for c in project.characters] if is_loaded(project, "characters") else [],
        "places": [serialize_place(p) for p in project.places] if is_loaded(project, "places") else [],
        "scenes": [serialize_scene(s) for s in project.scenes] if is_loaded(project, "scenes") else [],
        "voiceovers": [serialize_voiceover(v) for v in project.voiceovers] if is_loaded(project, "voiceovers") else [],
        "images_packages": [serialize_images_package(ip) for ip in project.images_packages] if is_loaded(project, "images_packages") else [],
        "background_music": [serialize_music(m) for m in project.background_music] if is_loaded(project, "background_music") else []
    }

def serialize_character(character: Character):
    return {
        "id": character.id,
        "name": character.name,
        "prompt": character.prompt,
        "src": character.src
    }

def serialize_place(place: Place):
    return {
        "id": place.id,
        "name": place.name,
        "prompt": place.prompt,
        "src": place.src
    }

def serialize_scene(scene: Scene):
    return {
        "id": scene.id,
        "project_id": scene.project_id,
        "video_prompt": scene.video_prompt,
        "video_src": scene.video_src,
        # Using the helper makes this cleaner
        "characters": [serialize_character(c) for c in scene.characters] if is_loaded(scene, "characters") else [],
        "places": [serialize_place(p) for p in scene.places] if is_loaded(scene, "places") else [],
        "images": [serialize_scene_image(i) for i in scene.images] if is_loaded(scene, "images") else [],
        
        "start_time": scene.start_time,
        "duration": scene.duration,
        "cut_start": scene.cut_start or 0.0,
        "cut_end": scene.cut_end or 0.0,
        "layer": scene.layer or 2
    }

def serialize_voiceover(voiceover: Voiceover):
    return {
        "id": voiceover.id,
        "project_id": voiceover.project_id,
        "text": voiceover.text,
        "text_with_pauses": voiceover.text_with_pauses,
        "src": voiceover.src,
        "timestamps": json.loads(voiceover.timestamps) if voiceover.timestamps else [],
        
        "start_time": voiceover.start_time,
        "duration": voiceover.duration,
        "cut_start": voiceover.cut_start or 0.0,
        "cut_end": voiceover.cut_end or 0.0,
        "layer": voiceover.layer or 3
    }
    
def serialize_music(music: Music):
    return {
        "id": music.id,
        "project_id": music.project_id,
        "name": music.name,
        "src": music.src,
        
        "start_time": music.start_time,
        "duration": music.duration,
        "cut_start": music.cut_start or 0.0,
        "cut_end": music.cut_end or 0.0,
        "layer": music.layer or 4
    }

def serialize_images_package(package: ImagesPackage):
    return {
        "id": package.id,
        "name": package.name,
        "created_at": package.created_at.isoformat() if package.created_at else None,
        "images": [serialize_photo_dump_image(img) for img in package.images] if is_loaded(package, "images") else []
    }

def serialize_photo_dump_image(image: PhotoDumpImage):
    return {
        "id": image.id,
        "prompt": image.prompt,
        "src": image.src
    }

def serialize_scene_image(image: SceneImage):
    return {
        "id": image.id,
        "time": image.time,
        "prompt": image.prompt,
        "src": image.src
    }

def serialize_settings(settings: Settings):
    return {
        "id": settings.id,
        "selected_tts_provider": settings.selected_tts_provider,
        "selected_llm_provider": settings.selected_llm_provider,
        "selected_diffusion_provider": settings.selected_diffusion_provider,
        "tts_provider_settings": json.loads(settings.tts_provider_settings) if settings.tts_provider_settings else {},
        "diffusion_provider_settings": json.loads(settings.diffusion_provider_settings) if settings.diffusion_provider_settings else {},
        "llm_provider_settings": json.loads(settings.llm_provider_settings) if settings.llm_provider_settings else {}
    }