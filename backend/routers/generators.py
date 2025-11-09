from fastapi import APIRouter, HTTPException, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import func
import uuid

import json

import os

from db import Place, get_session, Project, Scene, Character, Voiceover

from .prompts import gather_story_data, generate_story, story_split, add_scenes_to_story, prepare_story_for_db, get_persistant_characters, add_character_changes

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


class FixImagePrompt(BaseModel):
    prompt: str
    style: Optional[str]
    style_power: int


styles = {
    "lifelaps": (
        "hyper-realistic. "
        "Set in a dark, intimate night environment with deep shadows and low ambient light. "
        "Extreme photorealism with razor-sharp details on the main subject, cinematic shallow depth of field "
        "creating creamy bokeh in the blurred background. Dramatic low-key lighting: a strong, focused key light "
        "sculpting the face and body with rich contrast, subtle cool rim light separating the subject from the darkness, "
        "and faint warm accents for depth. Skin tones glow naturally under the light with visible texture and micro-details. "
        "Clean, modern aesthetic, perfect color grading with deep blacks, saturated highlights, "
        "and a moody teal-orange contrast for cinematic emotional impact. "
        "No holographic overlays, no glowing labels, no orbital paths, no molecular structures—pure photographic realism."
    ),
    "lifelaps_science": (
        "hyper-realistic. "
        "Set in a dark, futuristic lab at night with minimal ambient light and rich blackness. "
        "Extreme photorealism with razor-sharp details on the main subject, cinematic shallow depth of field "
        "creating creamy bokeh in the blurred background. Dramatic low-key lighting: a strong, focused key light "
        "sculpting the subject, subtle cool rim light, and faint warm fill for perfect skin tones and texture clarity. "
        "Subtle scientific holographic overlays float gently in the space around the subject: "
        "translucent glowing globes with soft descriptive labels, faint orbital paths, delicate molecular structures, "
        "and light data visualizations. These elements emit their own soft glow, enhancing the dark atmosphere "
        "without overpowering the subject. Deep volumetric light rays cut through the darkness, "
        "creating an immersive, high-tech aura. Clean, modern aesthetic, perfect color grading with deep blacks, "
        "neon accents, and a cool-warm contrast for emotional impact."
    ),
    "criminal": (
        "dark, cinematic noir with a mysterious and slightly unsettling aura — "
        "think high-stakes crime thriller, not horror. Use deep shadows, low-key lighting with a single dramatic light source "
        "(like a streetlamp, desk lamp, or moonlight cutting through blinds), desaturated colors dominated by cool blues, "
        "deep grays, and muted blacks with subtle accents of crimson or amber. Add atmospheric fog, light mist, or cigarette smoke "
        "drifting through beams of light. Sharp contrast, grainy film texture (35mm aesthetic), shallow depth of field "
        "to isolate the subject against a moody, blurred urban or industrial background. "
        "The mood is tense, secretive, and morally ambiguous — evoke suspicion, hidden motives, and quiet danger. "
        "Ultra-realistic skin textures, reflective wet surfaces, subtle lens flares, and micro-details in clothing and tools. "
        "No supernatural elements, no gore, no monsters — just raw human tension in a shadowy underworld."
    )
}

@router.post('/fix-scene-image-prompt')
async def fix_scene_image_prompt(request: FixImagePrompt):

    style = styles.get(request.style, False)    
    
    style_prompt = (
        f"Style description:\n"
        f"{style}\n\n"
        f"For the style: blend your expert creative judgment with the provided style description. "
        f"Apply it at intensity ({request.style_power}/10), where:\n"
        f"  • 1 = faint suggestion only\n"
        f"  • 5 = balanced, natural integration\n"
        f"  • 10 = dominant but still coherent\n\n"
        f"**CRITICAL RULE**: Never force any style element — no matter the intensity — if it damages realism, logic, or narrative coherence. "
        f"Lighting, color, mood, and composition are *always* non-negotiable foundations. "
        f"Any secondary effect (fog, grain, overlays, textures, etc.) must *earn its place*: "
        f"it is allowed **only if it actively strengthens the story, emotion, or visual impact** — "
        f"and **must be omitted** if it feels tacked-on, distracting, or out of context.\n\n"
        f"Your priority: a **professional, emotionally powerful, believable image** — "
        f"not a checklist. Style serves the scene. Never the reverse."
    )

    response = open_ai_client.chat.completions.create(
        model="gpt-4o-mini",
        response_model=FixedPromptResponse,
        messages=[
            {"role": "user", "content": (
                f"Scene description: {request.prompt}. "
                f"Correct this prompt to be suitable for AI image generation in JSON detailed description format. "
                f"{style_prompt if style else ''}"
            )}
        ]
    )
    fixed_prompt = response.fixed_prompt  # Access directly (Instructor parses it for you)
    print("Fixed prompt:", fixed_prompt)
    return {"fixed_prompt": fixed_prompt}


class FixVideoPrompt(BaseModel):
    image_prompt: str
    video_prompt: str

@router.post('/fix-scene-video-prompt')
async def fix_scene_video_prompt(request: FixVideoPrompt):
    response = open_ai_client.chat.completions.create(
        model="gpt-4o-mini",
        response_model=FixedPromptResponse,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert prompt engineer for image-to-video AI generation. "   
                )
            },
            {
                "role": "user",
                "content": (
                    "Create the perfect short motion prompt.\n"
                    f"Reference image (you can see this perfectly — NEVER describe anything in it):\n{request.image_prompt}\n\n"
                    f"Rough video idea (turn this into smooth, natural motion ONLY — no new elements):\n{request.video_prompt}\n\n"
                    "Output ONLY the motion prompt, nothing else."
                    "PURE MOTION AND CHANGE ONLY — nothing else.\n\n"
                    "STRICT RULES (never break them):\n"
                    "1. NEVER describe anything static that is already visible in the reference image "
                    "(objects, people, animals, buildings, clothing, colors, lighting, materials, background, etc.).\n"
                    "2. NEVER add new objects, plants, water, flowers, animals, people, or any element not explicitly mentioned in the rough video idea.\n"
                    "3. NEVER make statues, paintings, or any inanimate objects move, breathe, walk, talk, or show emotion.\n"
                    "4. ONLY describe what actually moves or changes according to the user's rough video idea: "
                    "camera movement, wind, fabric, hair, particles, light rays, shadows, dust, steam, fire, water (only if mentioned), etc.\n"
                    "5. DO NOT use any camera terms (zoom, pan, dolly, tilt, etc.) — describe the visual effect of movement instead.\n"
                    "6. DO NOT mention timing, keyframes, duration, or any technical terms.\n"
                    "7. Use vivid, poetic, sensory language.\n"
                    "8. Make everything feel like one single, continuous, living moment.\n\n"

                    "If the rough video idea asks for zero motion or is impossible with these rules, "
                    "write a prompt that describes only the tiniest natural atmospheric shifts (dust floating, faint heat haze, etc.)."
                )
            }
        ]
    )
    fixed_prompt = response.fixed_prompt  # Access directly (Instructor parses it for you)
    print("Fixed prompt:", fixed_prompt)
    return {"fixed_prompt": fixed_prompt}


class ProjectIn(BaseModel):
    title: str
    duration: int
    data: Optional[str]
    persistant_characters: bool
    reference_stories: Optional[str]

@router.post("/generate-script")
async def generate_script(request: ProjectIn, session: AsyncSession = Depends(get_session)):
    print("hello")
    print("Received project input:", request)
    
    
    # word_count = estimated word count approximating to 2 words per second.
    word_count = request.duration * 150 / 60

    try:
        if request.data:
            story_data = request.data
        else:
            story_data = gather_story_data(request.title).model_dump()
        print("-----story data--------")
        print(json.dumps(story_data, indent=2))

        story = generate_story(request.title, word_count, story_data, request.reference_stories).model_dump()["script"]

        splitted_story = story_split(story)
        print("-----story--------")
        print(json.dumps(splitted_story))


        story_with_scenes_model = add_scenes_to_story(splitted_story)
        story_with_scenes = story_with_scenes_model.model_dump()["story"]
        print("-----story with scenes--------")
        print(json.dumps(story_with_scenes, indent=2))

        story_database_data = prepare_story_for_db(story_with_scenes, splitted_story)
        print("-----story for database--------")
        print(json.dumps(story_database_data, indent=2))

        # story_data = "**Joachim Knycha\u0142a - \"Vampire of Bytom\"**\n\n**Introduction**  \n- Joachim Knycha\u0142a is infamously known as the \"Vampire of Bytom\" due to his gruesome crimes and the nickname deriving from media coverage.  \n- His story has become a part of Polish criminal folklore, highlighting the interplay of crime, psychology, and cultural narratives surrounding murderers.  \n\n**Timeline of Events**  \n- **1946**: Joachim Knycha\u0142a is born in Bytom, Poland. \n- **1964**: His first known criminal behavior occurs, leading to brushes with the law that foreshadow his later gruesome actions.  \n- **1965**: Knycha\u0142a begins a series of brutal murders. The first victim, a local woman, is discovered in an abandoned area.  \n- **1966**: Reports of multiple disappearances of women in Bytom prompt police investigations.  \n- **May 1966**: Knycha\u0142a is arrested following the discovery of the remains of several victims, leading to sensational media coverage.  \n- **1967**: Knycha\u0142a is tried and convicted. His trial reveals the horrific nature of his crimes and his psychological makeup.  \n- **1970**: Knycha\u0142a is sentenced to life imprisonment. His incarceration continues as he becomes a notorious figure in Polish criminal history.  \n\n**Key Figures**  \n- **Joachim Knycha\u0142a**: The central figure, a notorious Polish serial killer with a troubled past leading to his violent tendencies.  \n- **Law Enforcement**: Local police in Bytom who worked tirelessly to solve the case and apprehend Knycha\u0142a amid public fear.  \n- **Criminal Psychologists**: Experts brought in to understand Knycha\u0142a's mindset and motives, contributing to the field of criminal psychology.  \n\n**Historical Context**  \n- Post-World War II Poland was undergoing significant social and economic changes, with urban centers like Bytom experiencing crime waves.  \n- The rise of serial killings in the 1960s across Europe, including insights into the psychology of criminals and the impact of personal traumas.  \n- The media's role in sensationalizing crime and shaping public perception, leading to Knycha\u0142a's infamous nickname. \n\n**Nature of the Crimes**  \n- Knycha\u0142a's approach involved luring women to isolated areas under various pretenses, then brutally murdering them.  \n- Victims were primarily young females, fitting a pattern that intrigued investigators and the public alike.  \n- Analysis of Knycha\u0142a's crimes highlighted elements of sexual deviance and fantasies tied to power and control over his victims.  \n\n**Trial and Conviction**  \n- The trial drew significant media attention, reflecting societal fears and fascinations with violent crime.  \n- Prosecutors presented harrowing details of Knycha\u0142a's acts, leading to public outcry for justice and protection.  \n- Knycha\u0142a demonstrated detached behavior during the trial, exhibiting signs of psychopathy which later influenced psychological studies on serial killers.  \n\n**Notable Outcomes**  \n- Knycha\u0142a's case catalyzed discussions on mental health awareness, supported by the insights of psychologists studying his behavior.  \n- The crimes led to discussions about women's safety and policing in urban settings, resulting in changes in approach to crime prevention.  \n- Ongoing cultural impact, as Knycha\u0142a's story has been referenced in books, documentaries, and films focusing on true crime in Poland.  \n\n**Legends and Cultural Impact**  \n- Knycha\u0142a's nickname as the \"Vampire of Bytom\" persisted in popular culture, reinforcing his infamy and creating a legend surrounding his character.  \n- Stories of his actions have been utilized in cautionary tales about urban dangers, impacting community awareness regarding personal safety.  \n- The criminal case continues to be studied in criminology courses and psychological assessments, underlining the lasting significance of his violent history.  \n\n**Conclusion**  \n- Joachim Knycha\u0142a remains a complex figure in Polish criminal history, embodying themes of violence, psychological disturbance, and societal fears.  \n- His case serves not only as a record of heinous acts but as a point of reflection for understanding the factors leading to such extreme criminal behavior."

        # story_database_data = {
        #     "voiceovers": [
        #         {
        #         "content_with_pauses": None,
        #         "content": "[fearful]In the shadowy streets of Bytom, a chilling legend was born.",
        #         "duration": 4.8,
        #         "start_time": 0
        #         },
        #         {
        #         "content_with_pauses": None,
        #         "content": "Meet Joachim Knycha\u0142a, the man forever known as the \"Vampire of Bytom\".",
        #         "duration": 5.4,
        #         "start_time": 5.8
        #         },
        #         {
        #         "content_with_pauses": None,
        #         "content": "His story isn\u2019t just about a killer; it\u2019s about the darkness within us all.",
        #         "duration": 6.1,
        #         "start_time": 12.2
        #         },
        #         {
        #         "content_with_pauses": None,
        #         "content": " \nBorn in 1946, Knycha\u0142a\u2019s life began in a world recovering from war.",
        #         "duration": 5.3,
        #         "start_time": 20.299999999999997
        #         },
        #         {
        #         "content_with_pauses": None,
        #         "content": "But by just 17, he tipped into crime \u2014 the first glimpse into the chaos brewing inside him.",
        #         "duration": 7.6,
        #         "start_time": 26.599999999999998
        #         },
        #         {
        #         "content_with_pauses": None,
        #         "content": "Then, in 1965, the nightmare began. His first victim, a local woman, vanished without a trace.",
        #         "duration": 7.2,
        #         "start_time": 36.199999999999996
        #         },
        #         {
        #         "content_with_pauses": None,
        #         "content": " \nBut why did the disappearances continue? ",
        #         "duration": 2.8,
        #         "start_time": 44.4
        #         },
        #         {
        #         "content_with_pauses": None,
        #         "content": " <curious>Reports flooded in. Women were missing, the air thick with fear.</curious>",
        #         "duration": 5.5,
        #         "start_time": 48.199999999999996
        #         },
        #         {
        #         "content_with_pauses": None,
        #         "content": " \nIn May 1966, Knycha\u0142a was caught, his brutal acts laid bare for all to see.",
        #         "duration": 6.3,
        #         "start_time": 54.699999999999996
        #         },
        #         {
        #         "content_with_pauses": None,
        #         "content": " During the trial, he showed no remorse \u2014 just a coldness that sent shivers down the spines of everyone watching.",
        #         "duration": 8.8,
        #         "start_time": 62.99999999999999
        #         },
        #         {
        #         "content_with_pauses": None,
        #         "content": " But what drives a man to such depths of evil?",
        #         "duration": 4.1,
        #         "start_time": 72.8
        #         },
        #         {
        #         "content_with_pauses": None,
        #         "content": "  \nSentenced to life in prison in 1970, Knycha\u0142a became a symbol of a disturbed mind.",
        #         "duration": 6.5,
        #         "start_time": 78.89999999999999
        #         },
        #         {
        #         "content_with_pauses": None,
        #         "content": " His case changed how we viewed mental health and safety for women in our cities.",
        #         "duration": 6.5,
        #         "start_time": 86.39999999999999
        #         },
        #         {
        #         "content_with_pauses": None,
        #         "content": " Today, as stories of him circulate, we\u2019re left to wonder: ",
        #         "duration": 4.4,
        #         "start_time": 93.89999999999999
        #         },
        #         {
        #         "content_with_pauses": None,
        #         "content": " how can a person embody such darkness? ",
        #         "duration": 3.1,
        #         "start_time": 99.3
        #         },
        #         {
        #         "content_with_pauses": None,
        #         "content": "But in the end, maybe he teaches us something vital about understanding the shadows that lurk, not just outside, but within ourselves.",
        #         "duration": 10.0,
        #         "start_time": 104.39999999999999
        #         }
        #     ],
        #     "scenes": [
        #         {
        #         "image_prompt": "A dimly lit street in Bytom, with fog swirling through the air, creating an eerie atmosphere. The cobblestone path is wet from rain, reflecting faint streetlights, while shadows loom ominously.",
        #         "video_prompt": "Camera slowly pans down the empty street, the sound of distant footsteps echoing in the silence as fog rolls in slowly, enhancing the fear.",
        #         "duration": 6,
        #         "start_time": 0.0
        #         },
        #         {
        #         "image_prompt": "A close-up of a dark, brooding man with piercing eyes, set against a stark wall covered in graffiti. His expression is intense, hinting at his troubled soul.",
        #         "video_prompt": "Camera zooms in on Knycha\u00142a's face, capturing every detail, as the lighting shifts to cast dark shadows across his features, symbolizing his inner turmoil.",
        #         "duration": 7,
        #         "start_time": 5.8
        #         },
        #         {
        #         "image_prompt": "A blend of faces, each expressing fear and confusion, fading in and out. The background is a dark, abstract representation of chaos and despair.",
        #         "video_prompt": "Camera shifts quickly between the faces, creating a sense of unease as unsettling music plays, highlighting the theme of internal darkness.",
        #         "duration": 8,
        #         "start_time": 12.2
        #         },
        #         {
        #         "image_prompt": "An old, sepia-toned photograph of a post-war era, featuring children playing in the rubble of a bombed-out building, filled with potential and sadness.",
        #         "video_prompt": "A slow fade from the photograph to black and white footage of a city slowly rebuilding, with somber music accompanying the transition.",
        #         "duration": 7,
        #         "start_time": 20.299999999999997
        #         },
        #         {
        #         "image_prompt": "A teenage boy in a dark alley, hands stuffed in his pockets, looking anxious and conflicted, with graffiti on the walls that signal danger.",
        #         "video_prompt": "Camera follows the boy as he furtively glances around before stepping deeper into the alley, accompanied by tense music detailing his descent into crime.",
        #         "duration": 5,
        #         "start_time": 26.599999999999998
        #         },
        #         {
        #         "image_prompt": "A newspaper headline shouting news of crimes involving youth, displayed on a cluttered table with a flickering lamp, signifying alertness and danger.",
        #         "video_prompt": "A hand slams down on the table, scattering papers, as a shadow looms over the scene, emphasizing the passage into chaos.",
        #         "duration": 4,
        #         "start_time": 31.599999999999998
        #         },
        #         {
        #         "image_prompt": "A serene street where a woman walks alone at night, illuminated by streetlights, creating a stark contrast to her impending fate.",
        #         "video_prompt": "Camera tracks her movements from behind before cutting sharply to black, signaling her disappearance and creating suspense.",
        #         "duration": 5,
        #         "start_time": 36.199999999999996
        #         },
        #         {
        #         "image_prompt": "A poster on a city wall, displaying the face of the missing woman, with community members gathered around it, their expressions filled with concern.",
        #         "video_prompt": "Camera zooms in on the poster as whispers surround the edges, showing the community's fear and disbelief about her vanishing.",
        #         "duration": 4,
        #         "start_time": 41.199999999999996
        #         },
        #         {
        #         "image_prompt": "A darkened room filled with newspapers and photos of missing women, all pinned on a wall like a disturbing collage, reflecting a sense of mystery.",
        #         "video_prompt": "Camera glides through the room, focusing on each photo while spotlighting the tension in the silence.",
        #         "duration": 5,
        #         "start_time": 44.4
        #         },
        #         {
        #         "image_prompt": "An urgent news reporter in a dimly lit studio, passionately speaking into the camera as images of missing persons flash behind him on a screen.",
        #         "video_prompt": "Camera cuts between the reporter and dramatic footage of frightened women, with fast-paced editing raising tension.",
        #         "duration": 6,
        #         "start_time": 48.199999999999996
        #         },
        #         {
        #         "image_prompt": "Concerned citizens gathered in a small community meeting, fear etched on their faces, as they share stories of missing loved ones.",
        #         "video_prompt": "Camera captures the anxious expressions of mothers and neighbors, interspersed with close-ups of trembling hands.",
        #         "duration": 5,
        #         "start_time": 54.199999999999996
        #         },
        #         {
        #         "image_prompt": "A crowded courtroom with a judge presiding sternly, while the defendant, Knycha\u00142a, sits with a cold, detached expression.",
        #         "video_prompt": "Camera pans over the audience, capturing shocked faces, then zooms in on Knycha\u00142a as the verdict is delivered.",
        #         "duration": 6,
        #         "start_time": 54.699999999999996
        #         },
        #         {
        #         "image_prompt": "A newspaper front page declaring 'The Vampire of Bytom Caught!' highlights the chaos surrounding his arrest.",
        #         "video_prompt": "The camera rapidly flips through the pages of a newspaper stack, drawing attention to the sensational headlines.",
        #         "duration": 4,
        #         "start_time": 60.699999999999996
        #         },
        #         {
        #         "image_prompt": "Knycha\u00142a sitting in the defendant's chair, expressionless and cold, surrounded by glaring eyes of the jury and spectators.",
        #         "video_prompt": "Camera closes in on his emotionless face, contrasting sharply with the gasps and whispers from the crowd.",
        #         "duration": 7,
        #         "start_time": 62.99999999999999
        #         },
        #         {
        #         "image_prompt": "Close-up of a juror's face reflecting horror and disbelief as evidence is presented, highlighting the tension within the courtroom.",
        #         "video_prompt": "Slow motion as the juror swallows, eyes wide, symbolizing the weight of the trial's revelations.",
        #         "duration": 4,
        #         "start_time": 70.0
        #         },
        #         {
        #         "image_prompt": "A shadowy figure standing alone in a darkened hallway, with distorted shadows looming as if they reflect inner evil.",
        #         "video_prompt": "Camera slowly zooms out, enhancing the figure's isolation within the darkness, creating an unsettling atmosphere.",
        #         "duration": 4,
        #         "start_time": 72.8
        #         },
        #         {
        #         "image_prompt": "A montage of dark scenes showing chaos engaging in society \u2014 crimes, fears, and shadows lurking behind each scene.",
        #         "video_prompt": "Quick cuts of tension-filled snippets, representing the question of evil within the human spirit.",
        #         "duration": 3,
        #         "start_time": 76.8
        #         },
        #         {
        #         "image_prompt": "An iron barred prison cell, dimly lit, with Knycha\u00142a sitting on the edge of his bed, staring blankly at the wall.",
        #         "video_prompt": "The camera slowly moves in on him, conveying his isolation and the weight of his actions as shadows flicker behind him.",
        #         "duration": 5,
        #         "start_time": 78.89999999999999
        #         },
        #         {
        #         "image_prompt": "A news report headlining \u2018Evil Personified: Knycha\u00142a\u2019s Sentence\u2019, with a montage of public reactions showcased.",
        #         "video_prompt": "Footage of protests and rallies, where citizens demand justice and safety, capturing the unrest surrounding his case.",
        #         "duration": 4,
        #         "start_time": 83.89999999999999
        #         },
        #         {
        #         "image_prompt": "A psychiatrist's office filled with mental health posters about awareness and understanding, showing a concerned therapist speaking.",
        #         "video_prompt": "Camera focuses on the therapist gesturing emphatically, with a split-screen showcasing news clips of women empowering each other.",
        #         "duration": 6,
        #         "start_time": 86.39999999999999
        #         },
        #         {
        #         "image_prompt": "A vibrant community march advocating for women\u2019s safety, filled with colorful banners and determined faces.",
        #         "video_prompt": "Camera sweeps through the crowd, capturing the energy and resolve of the community reacting to the past, unwilling to forget.",
        #         "duration": 5,
        #         "start_time": 92.39999999999999
        #         },
        #         {
        #         "image_prompt": "A dark, empty street at night, a dim streetlight flickering, casting shadows as whispers of Knycha\u00142a's legend echo.",
        #         "video_prompt": "Camera pans slowly down the street, creating a sense of eerie solitude, while the echoes of conversations can be faintly heard.",
        #         "duration": 4,
        #         "start_time": 93.89999999999999
        #         },
        #         {
        #         "image_prompt": "A collection of old books and articles laid out on a table, with a candle flickering, illuminating the text about Knycha\u00142a.",
        #         "video_prompt": "Camera zooms in on the text as if inviting the viewer to delve deeper into the chilling tale, with wind softly stirring the pages.",
        #         "duration": 3,
        #         "start_time": 97.89999999999999
        #         },
        #         {
        #         "image_prompt": "A person walking alone on a dark path, with glimmers of light breaking through the trees, symbolizing hope against the darkness.",
        #         "video_prompt": "Camera follows the person's footsteps, highlighting the uncertainty of the night, capturing inner questions through the pace.",
        #         "duration": 4,
        #         "start_time": 99.3
        #         },
        #         {
        #         "image_prompt": "A close-up of a flickering candle illuminating a dark room, casting long shadows on the wall, representing the internal struggle.",
        #         "video_prompt": "Camera lingers on the candle's flame, creating an ambiance of introspection as the shadows dance around it.",
        #         "duration": 3,
        #         "start_time": 103.3
        #         },
        #         {
        #         "image_prompt": "A serene landscape at dawn, with light slowly breaking through the darkness, symbolizing hope and understanding.",
        #         "video_prompt": "Camera captures the sunrise, illuminating the landscape, accompanied by uplifting music that represents awakening and realization.",
        #         "duration": 7,
        #         "start_time": 104.39999999999999
        #         },
        #         {
        #         "image_prompt": "A group of diverse individuals engaging in a community discussion, sharing experiences and building understanding over coffee.",
        #         "video_prompt": "Camera moves gently around the group, focusing on their evolving bond as heartfelt conversations unfold, showcasing healing and support.",
        #         "duration": 5,
        #         "start_time": 111.39999999999999
        #         }
        #     ]
        # }

        if request.persistant_characters:
            scene_image_prompts = [scene["image_prompt"] for scene in story_database_data["scenes"]]
            character_changes = get_persistant_characters(scene_image_prompts, story_data)
            print("-----character changes-------")
            print(json.dumps(character_changes, indent=2))
            add_character_changes(story_database_data, character_changes)
    

        # character_changes = {
        #     "persistant_characters": [
        #         {
        #         "name": "Joachim Knycha\u0142a",
        #         "image_prompt": "Reference image: Joachim Knycha\u0142a\nReference image contains face of the character\nGeneral description: lean, 50-something Polish male, approximately 175 cm, graying hair, sharp features, intense gaze\nClothing: tattered prison uniform, bare feet, subdued colors reflecting his incarceration\nPose & framing: full-body, neutral standing pose, 3/4 view, visible hands and feet, head-to-toe in frame\nBackground: white background",
        #         "scenes": [
        #             12,
        #             13,
        #             16,
        #             18
        #         ]
        #         }
        #     ],
        #     "changed_scenes": [
        #         {
        #         "scene_index": 3,
        #         "new_image_prompt": "An old, sepia-toned photograph of a post-war era, featuring children playing in the rubble of a bombed-out building, filled with potential and sadness. Reference image of Joachim Knycha\u0142a"
        #         },
        #         {
        #         "scene_index": 4,
        #         "new_image_prompt": "A teenage boy in a dark alley, hands stuffed in his pockets, looking anxious and conflicted, with graffiti on the walls that signal danger. Reference image of Joachim Knycha\u0142a"
        #         },
        #         {
        #         "scene_index": 18,
        #         "new_image_prompt": "A darkened room filled with newspapers and photos of missing women, all pinned on a wall like a disturbing collage, reflecting a sense of mystery. Reference image of Joachim Knycha\u0142a"
        #         }
        #     ]
        # }


        print("-----story with scenes and characters--------")
        print(json.dumps(story_database_data, indent=2))

        project = Project(
            id=str(uuid.uuid4()),
            name=request.title,
            created_at=func.now()
        )

        session.add(project)

        print("added project")
        if(request.persistant_characters):
            characters_map = {}
            for character in story_database_data["characters"]:
                character_db = Character(
                    id=str(uuid.uuid4()),
                    prompt = character["image_prompt"],
                    name = character["name"]
                )
                session.add(character_db)
                characters_map[character["name"]] = character_db
                project.characters.append(character_db)

        print("added characters")
        for scene in story_database_data["scenes"]:
            scene_db = Scene(
                id=str(uuid.uuid4()),
                duration=scene["duration"],
                start_time=scene["start_time"],
                image_prompt=scene["image_prompt"],
                video_prompt=scene["video_prompt"],
                project_id=project.id
            )
            session.add(scene_db)

            if "characters" in scene:
                for char_name in scene["characters"]:
                    if char_name in characters_map:
                        scene_db.characters.append(characters_map[char_name])


        print("added scenes")
        for voiceover in story_database_data["voiceovers"]:
            voiceover_db = Voiceover(
                id=str(uuid.uuid4()),
                text=voiceover["content"],
                text_with_pauses=voiceover["content_with_pauses"],
                project_id=project.id,
                start_time=voiceover["start_time"],  # Adjust based on scene timing if needed
                duration=voiceover["duration"],
                timestamps=None
            )
            session.add(voiceover_db)

        print("added voiceovers")


        await session.commit()

        return {"Success": True}


        # scenes = generate_scenes(story_data, voiceover_timeline)
        # project_out = get_full_project(story_data, voiceover_timeline, scenes)

        print("saving the project")
        # Create new Project in database
     
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