from fastapi import APIRouter, HTTPException, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import func
import uuid

import json

import os

from db import Place, get_session, Project, Scene, Character, Voiceover

from .prompts import gather_story_data, generate_story, story_split, add_scenes_to_story, prepare_story_for_db

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
    topic: str
    duration: int

@router.post("/generate-script")
async def generate_script(request: ProjectIn, session: AsyncSession = Depends(get_session)):
    print("hello")
    print("Received project input:", request)
    
    
    # word_count = estimated word count approximating to 2 words per second.
    word_count = request.duration * 2

    try:

        # story_data = gather_story_data(request.topic)
        # voiceover_timeline = generate_story(request.topic, word_count, story_data)
        
        story = "In the shadowy alleys of Krak\u00f3w, Poland, a chilling figure roamed. His name was Karol Kot, forever etched in infamy as the \"Vampire of Krak\u00f3w\". <break time=\"1s\"/> Born on December 1, 1946, he seemed like any other boy, growing up in a middle-class family. But beneath a facade of normalcy lay a mind twisted by violence and obsession. <break time=\"1s\"/> In late 1964, he lured a mere 15-year-old girl named Teresa K. with empty promises, pulling her into a dark secret by the Wis\u0142a River. <break time=\"2s\"/> What happened next would haunt the city forever... <break time=\"1s\"/> His second victim arrived swiftly\u2014a 16-year-old girl, too trusting of his charm. The brutality of these acts earned him the nickname \"Vampire,\" not for fangs, but for the blood he spilled. <break time=\"1s\"/> By March 1966, police pieced together the horror, leading to his capture. <break time=\"2s\"/> During interrogation, his chilling confession revealed a twisted thrill in his actions, sparking a mix of fear and fascination across Poland. <break time=\"1s\"/> His trial captured public attention\u2014where he feebly pleaded insanity, claiming he wasn't fully accountable.<break time=\"1s\"/>  Found guilty, he faced a grim fate, executed by firing squad at just 21 years old. <break time=\"1s\"/> Today, the legacy of the \"Vampire of Krak\u00f3w\" serves as a haunting reminder of the darkness that can exist within, intertwining crime with culture, forever captivating true crime enthusiasts."

        splitted_story = story_split(story)


        story_with_scenes = [
            {
            "content": "In the shadowy alleys of Krak\u00f3w, Poland, a chilling figure roamed",
            "duration": 8.0,
            "scenes": [
                {
                "image_prompt": "A narrow, dimly-lit alley in Krak\u00f3w, mist swirling near the cobblestones under flickering street lamps. Shadows from the buildings create a sense of foreboding.",
                "video_prompt": "The camera slowly pans down the alley as a silhouette moves in the distance, hinting at the presence of a sinister figure.",
                "duration": 4
                },
                {
                "image_prompt": "Close-up of a looming figure, partially hidden in the shadows, with an ominous aura surrounding him, hinting at malice.",
                "video_prompt": "A slow zoom towards the figure\u2019s face, revealing a smirk that disappears into darkness.",
                "duration": 4
                }
            ]
            },
            {
            "content": "His name was Karol Kot, forever etched in infamy as the \"Vampire of Krak\u00f3w\"",
            "duration": 9.0,
            "scenes": [
                {
                "image_prompt": "A dark library setting with an open book displaying 'Karol Kot \u2013 The Vampire of Krak\u00f3w', illuminated by a single beam of light.",
                "video_prompt": "Camera slowly zooms in on the book as pages turn, revealing images of the Krak\u00f3w skyline.",
                "duration": 4
                },
                {
                "image_prompt": "A portrait of Karol Kot, somber and eerie, against a backdrop of historic Krak\u00f3w, blending beauty and horror.",
                "video_prompt": "Camera moves upwards from the portrait, revealing the skyline of Krak\u00f3w at dusk, casting a spooky ambiance.",
                "duration": 5
                }
            ]
            },
            {
            "content": "Born on December 1, 1946, he seemed like any other boy, growing up in a middle-class family",
            "duration": 11.0,
            "scenes": [
                {
                "image_prompt": "A serene suburban home in 1950s Krak\u00f3w, with children playing in the yard, laughter in the air, showcasing innocence.",
                "video_prompt": "Camera pans across the yard, focusing on a young Karol playing happily, creating a stark contrast to the future events.",
                "duration": 6
                },
                {
                "image_prompt": "A melancholic interior of a family dining room, the atmosphere heavy with tension and unspoken words.",
                "video_prompt": "The camera slowly zooms in on an empty chair at the table, suggesting a missing presence.",
                "duration": 5
                }
            ]
            },
            {
            "content": "But beneath a facade of normalcy lay a mind twisted by violence and obsession",
            "duration": 9.0,
            "scenes": [
                {
                "image_prompt": "Close-up of a thoughtful boy's face, eyes dark with hidden thoughts, framed by dramatic shadows.",
                "video_prompt": "The camera tightens on his face as a flicker of rage crosses his features, then fades away, settling back into a blank expression.",
                "duration": 5
                },
                {
                "image_prompt": "A stark contrast: a torn childhood drawing revealing dark, disturbing imagery hidden amongst innocent doodles.",
                "video_prompt": "Slow pan across the drawing, focusing on the disturbing parts, with ominous music building in the background.",
                "duration": 4
                }
            ]
            },
            {
            "content": "In late 1964, he lured a mere 15-year-old girl named Teresa K",
            "duration": 7.0,
            "scenes": [
                {
                "image_prompt": "A vulnerable teenage girl standing by a playground, a hint of hesitation in her eyes while looking off into the distance.",
                "video_prompt": "The camera circles around her, illustrating her naivety and the looming danger.",
                "duration": 4
                },
                {
                "image_prompt": "Karol Kot, charismatic yet chilling, leans against a tree, a sly smile, with dim lighting highlighting his menacing features.",
                "video_prompt": "The camera moves in closer to capture his confidence and sinister charm as he watches Teresa.",
                "duration": 3
                }
            ]
            },
            {
            "content": "with empty promises, pulling her into a dark secret by the Wis\u0142a River",
            "duration": 8.0,
            "scenes": [
                {
                "image_prompt": "A serene view of the Wis\u0142a River at twilight, tranquil yet eerie, with shadows hanging in the trees.",
                "video_prompt": "Camera slowly glides over the water's surface, evoking a sense of foreboding as the light begins to fade.",
                "duration": 4
                },
                {
                "image_prompt": "Karol and Teresa at the riverbank, with lush greenery around them, yet the scene feels heavy and foreboding.",
                "video_prompt": "The camera pans back, showcasing a slowly creeping fog enveloping the area, adding to the sense of danger.",
                "duration": 4
                }
            ]
            },
            {
            "content": "What happened next would haunt the city forever",
            "duration": 6.0,
            "scenes": [
                {
                "image_prompt": "An empty Krak\u00f3w street under a moonlit sky, silence and stillness, with a faint echo of distant cries.",
                "video_prompt": "Camera tracks backward through the street, emphasizing the eerie quietude, building suspense.",
                "duration": 3
                },
                {
                "image_prompt": "A darkened newspaper stand with headlines screaming of horror, while the image of the city fades into the background.",
                "video_prompt": "The camera focuses tightly on the headlines, with small raindrops blurring the paper, enhancing the somber mood.",
                "duration": 3
                }
            ]
            },
            {
            "content": "His second victim arrived swiftly\u2014a 16-year-old girl, too trusting of his charm",
            "duration": 9.0,
            "scenes": [
                {
                "image_prompt": "A young girl innocently laughing with friends, the sun shining, creating a light-hearted scene that feels too good to be true.",
                "video_prompt": "The camera slowly zooms in on her radiant smile, masking the danger that lurks nearby.",
                "duration": 4
                },
                {
                "image_prompt": "Karol, observing from a distance with an unsettling gaze, his smile revealing a predatory nature.",
                "video_prompt": "Camera slowly tilts down from the girl to him, enhancing the tension between innocence and malevolence.",
                "duration": 5
                }
            ]
            },
            {
            "content": "The brutality of these acts earned him the nickname \"Vampire,\" not for fangs, but for the blood he spilled",
            "duration": 12.0,
            "scenes": [
                {
                "image_prompt": "A montage: blood-red splashes against a white canvas, becoming more vivid and disjointed, creating a startling visual representation.",
                "video_prompt": "Fast-cut transitions of blood drops hitting the canvas with rising melancholic music, depicting horror.",
                "duration": 6
                },
                {
                "image_prompt": "Image of terrified citizens reading about the crimes in the newspaper, with expressions of fear and disbelief etched on their faces.",
                "video_prompt": "Camera slowly zooms in on one person's face, capturing the horror dawning in their eyes as they read.",
                "duration": 6
                }
            ]
            },
            {
            "content": "By March 1966, police pieced together the horror, leading to his capture",
            "duration": 8.0,
            "scenes": [
                {
                "image_prompt": "A confining police interrogation room, two detectives scrutinizing a shadowy figure behind bars, the atmosphere tense and oppressive.",
                "video_prompt": "Camera moves from the detectives to the figure in the cell, highlighting the grim reality of the situation.",
                "duration": 5
                },
                {
                "image_prompt": "Police officers pinning up photographs of victims on a notice board, showcasing the gruesome timeline of events.",
                "video_prompt": "The camera crisscrosses across the board, emphasizing names and dates, creating a harrowing atmosphere.",
                "duration": 3
                }
            ]
            },
            {
            "content": "During interrogation, his chilling confession revealed a twisted thrill in his actions, sparking a mix of fear and fascination across Poland",
            "duration": 16.0,
            "scenes": [
                {
                "image_prompt": "Karol Kot in the interrogation chair, face illuminated dramatically, showing a chilling mixture of pride and insanity.",
                "video_prompt": "The camera slowly zooms in on his facial expressions as he speaks, laced with madness, creating an unsettling tension.",
                "duration": 5
                },
                {
                "image_prompt": "Images of newspaper headlines and reports rushing into view, alongside crowds reflecting fear and intrigue.",
                "video_prompt": "Camera swiftly shifts between newspaper clippings and crowds, creating a chaotic yet connected portrayal of public reaction, with rising intensity.",
                "duration": 6
                },
                {
                "image_prompt": "A stark scene of legal documents piled on a table, incongruous with the horror they represent, invoking a sense of tragedy.",
                "video_prompt": "The camera glides over the documents, lingering on disturbing phrases and visuals associated with the case.",
                "duration": 5
                }
            ]
            },
            {
            "content": "His trial captured public attention\u2014where he feebly pleaded insanity, claiming he wasn't fully accountable",
            "duration": 12.0,
            "scenes": [
                {
                "image_prompt": "The courtroom packed with onlookers, faces filled with anticipation and horror, as Karol sits in the defendant's chair, head hung low.",
                "video_prompt": "Camera slowly tracks across the courtroom, capturing the nervous energy and fear in the air.",
                "duration": 6
                },
                {
                "image_prompt": "A close-up of Karol\u2019s expression, his eyes darting between the judge and the audience, pleading incompetently.",
                "video_prompt": "The camera zooms in on his pleading gesture, accentuating the desperation and denial.",
                "duration": 6
                }
            ]
            },
            {
            "content": "Found guilty, he faced a grim fate, executed by firing squad at just 21 years old",
            "duration": 10.0,
            "scenes": [
                {
                "image_prompt": "The gory backdrop of a firing squad preparing, dark clouds overhead signaling an impending storm, a sense of foreboding looming.",
                "video_prompt": "Camera pans across soldiers, highlighting their tense faces as they prepare their weapons, emphasizing the dread.",
                "duration": 5
                },
                {
                "image_prompt": "A close-up of Karol before execution, a mixture of fear and defiance in his eyes, against a backdrop of shadowy figures.",
                "video_prompt": "Camera slowly zooms into his eyes, capturing the conflicting emotions in the final moments.",
                "duration": 5
                }
            ]
            },
            {
            "content": "Today, the legacy of the \"Vampire of Krak\u00f3w\" serves as a haunting reminder of the darkness that can exist within, intertwining crime with culture, forever captivating true crime enthusiasts",
            "duration": 22.0,
            "scenes": [
                {
                "image_prompt": "A mournful Krak\u00f3w at twilight, historical sites silhouetted against a darkening sky, embodying the city's haunting past.",
                "video_prompt": "Camera slowly pans over the skyline, with ghosts of the past felt in the air, creating a reflective tone.",
                "duration": 7
                },
                {
                "image_prompt": "Artifacts displayed in a museum, a showcase of the 'Vampire of Krak\u00f3w', chilling yet captivating perfect for true crime enthusiasts.",
                "video_prompt": "The camera moves through the exhibit, highlighting each item with low lighting and somber music, evoking curiosity mixed with horror.",
                "duration": 7
                },
                {
                "image_prompt": "A group of true crime enthusiasts discussing passionately among the artifacts, their faces illuminated by soft light showing intrigue and shock.",
                "video_prompt": "Camera circles around the group, capturing their expressions and gestures, blending fascination with storytelling.",
                "duration": 8
                }
            ]
            }
        ]

        story_database_data = prepare_story_for_db(story_with_scenes, splitted_story)


        print(json.dumps(story_database_data, indent=2))

        return {"Success": True}


        # scenes = generate_scenes(story_data, voiceover_timeline)
        # project_out = get_full_project(story_data, voiceover_timeline, scenes)

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