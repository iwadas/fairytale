from fastapi import APIRouter, HTTPException, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import func
import uuid

import os

from db import Place, get_session, Project, Scene, Character, Voiceover

from .prompts import gather_story_data, generate_voiceovers, generate_scenes, get_full_project

from schemas import PromptRequest, FixedPromptResponse
from pydantic import BaseModel
from typing import Optional, List

from openai import OpenAI
import instructor
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
open_ai_client = instructor.from_openai(OpenAI(api_key=OPENAI_API_KEY))

router = APIRouter(prefix="/generators", tags=["generators"])

@router.post('/fix-character-prompt')
async def fix_character_prompt(request: PromptRequest):
    print("Something")
    print("Original prompt:", request.prompt)

    response = open_ai_client.chat.completions.create(
        model="gpt-4o-mini",
        response_model=FixedPromptResponse,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that improves character descriptions for AI image generation. Your output should be an JSON description of scene that will be used for AI image generation"},
            {"role": "user", "content": request.prompt}
        ]
    )
    fixed_prompt = response.fixed_prompt  # Access directly (Instructor parses it for you)
    print("Fixed prompt:", fixed_prompt)
    return {"fixed_prompt": fixed_prompt}


class VideoPromptRequest(BaseModel):
    image_prompt: str
    video_prompt: str

@router.post('/fix-scene-image-prompt')
async def fix_scene_image_prompt(request: PromptRequest):
    response = open_ai_client.chat.completions.create(
        model="gpt-4o-mini",
        response_model=FixedPromptResponse,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that improves scene image prompts for AI image generation."},
            {"role": "user", "content": "Scene description: " +request.prompt + ". Correct this prompt to be suitable for AI image generation in JSON detailed description format."}
        ]
    )
    fixed_prompt = response.fixed_prompt  # Access directly (Instructor parses it for you)
    print("Fixed prompt:", fixed_prompt)
    return {"fixed_prompt": fixed_prompt}

@router.post('/fix-scene-video-prompt')
async def fix_scene_video_prompt(request: PromptRequest):
    response = open_ai_client.chat.completions.create(
        model="gpt-4o-mini",
        response_model=FixedPromptResponse,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant that improves scene video prompts for AI video generation. "
                    "Ensure the improved prompt uses simple, easy transitions to avoid errors in generation. "
                    "Focus on making the prompt entertaining, maximizing the model's output quality without risking poor results. "
                    "Stick to straightforward descriptions that are highly understandable for the AI model."
                )
            },
            {
                "role": "user",
                "content": (
                    "What is in the image: " + request.image_prompt +
                    "Scene video prompt: " + request.video_prompt + 
                    ". Correct this prompt to be suitable for AI video generation in JSON detailed description format."
                )
            }
        ]
    )
    fixed_prompt = response.fixed_prompt  # Access directly (Instructor parses it for you)
    print("Fixed prompt:", fixed_prompt)
    return {"fixed_prompt": fixed_prompt}



class ProjectIn(BaseModel):
    title: str  # Topic/story title
    style: str  # e.g., "epic fantasy", "noir thriller"
    voiceover_style: str  # e.g., "dramatic", "calm"
    prompt: str
    duration: int = 10  # Total film duration in seconds

@router.post("/generate-script")
async def generate_script(request: ProjectIn, session: AsyncSession = Depends(get_session)):
    print("hello")
    print("Received project input:",)
    
    
    try:
        
        story_data = gather_story_data(request.prompt)
        voiceover_timeline = generate_voiceovers(story_data, request.duration)
        scenes = generate_scenes(story_data, voiceover_timeline)
        project_out = get_full_project(story_data, voiceover_timeline, scenes)

        print("saving the project")
        # Create new Project in database
        project = Project(
            id=str(uuid.uuid4()),
            name=request.title,
            created_at=func.now()
        )
        session.add(project)

        # Save Characters
        character_map = {}  # To map character IDs to DB objects
        for char_out in project_out.characters:
            character = Character(
                id=str(uuid.uuid4()),
                name=char_out.name,
                prompt=char_out.prompt
            )
            session.add(character)

            # Assiciation between characters and scenes
            # character_map[char_out.id] = character
           
            # Associate character with project
            project.characters.append(character)

        # Save Places
        place_map = {}  # To map place names to DB objects
        for place_out in project_out.places:
            if place_out.name not in place_map:
                place = Place(
                    id=str(uuid.uuid4()),
                    name=place_out.name,
                    prompt=place_out.prompt,
                    src=""  # Placeholder, to be generated later
                )
                # Associate place with project
                session.add(place)
                # place_map[place_out.id] = place
                project.places.append(place)


        # Save Scenes and associate Characters
        for scene_out in project_out.scenes:
            scene = Scene(
                id=str(uuid.uuid4()),
                scene_number=scene_out.scene_number,
                duration=scene_out.duration,
                image_prompt=scene_out.image_prompt,
                video_prompt=scene_out.video_prompt,
                project_id=project.id
            )
            session.add(scene)
            # Associate characters with scene
            # for char_id in scene_out.character_ids:
            #     if char_id in character_map:
            #         scene.characters.append(character_map[char_id])
            # for place_id in scene_out.places_ids:
            #     if place_id in place_map:
            #         scene.places.append(place_map[place_id])

        # Save Voiceovers
        for vo_out in project_out.voiceovers:
            voiceover = Voiceover(
                id=str(uuid.uuid4()),
                text=vo_out.text,
                project_id=project.id,
                start_time=vo_out.start_time,  # Adjust based on scene timing if needed
                duration=vo_out.duration
            )
            session.add(voiceover)

        # Commit all changes
        await session.commit()

        # RETURN PROJECT OUTPUT ID
        return {"project_id": project.id}

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))