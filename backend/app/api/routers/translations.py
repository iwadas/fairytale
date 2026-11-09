import logging
from openai import OpenAI
import instructor
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json  
import re
from app.media.storage import generate_speech, filename_from_name  # FIXME(cleanup): generate_speech, filename_from_name no longer exist
import uuid

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_settings = get_settings()
OPENAI_API_KEY = _settings.openai_api_key.get_secret_value() if _settings.openai_api_key is not None else None
open_ai_client = instructor.from_openai(OpenAI(api_key=OPENAI_API_KEY))

LANGUAGES = [
    {
        "name": "Polish",
        "code": "PL",
        "voice_id": "o2xdfKUpc1Bwq7RchZuW"
    },
    # {
    #     "name": "English",
    #     "code": "EN",
    #     "voice_id": "Cz0K1kOv9tD8l0b5Qu53",
    # },
    # {
    #     "name": "Spanish",
    #     "code": "ES",
    #     "voice_id": "efcRUax7uSa9kpBwtDPe",
    # },
    # {
    #     "name": "German",
    #     "code": "DE",
    #     "voice_id": "kkJxCnlRCckmfFvzDW5Q",
    # }
]

class TranslatedVoiceover(BaseModel):
    text: str
    start_time: float

class TranslatedVoiceovers(BaseModel):
    voiceovers: List[TranslatedVoiceover]

def get_translated_voiceovers(language_index, voiceovers):

    if language_index >= len(LANGUAGES):
        return None
    
    selected_language = LANGUAGES[language_index]

    voiceovers_for_prompt = [
        {
            "text": vo["text"],
            "start_time": vo["start_time"],
        }
        for vo in voiceovers
    ]

    messages = [
        {
            "role": "system",
            "content": (
                f"You are a professional translator specializing in natural, human-like translations "
                f"from English to {selected_language['name']}. Your goal is to make the translated text "
                f"sound like a fluent voiceover in a movie—smooth, emotional, and natural, not literal."
            )
        },
        {
            "role": "user",
            "content": (
                "Translate each entry inside voiceovers.text.\n"
                "Do NOT translate the start_time value.\n"
                "Focus on making the translation sound natural, cinematic, and appropriate for spoken dialogue.\n"
                "Feel free to adjust wording for flow, but keep the original meaning and tone.\n\n"
                "Here are the voiceovers to translate (keep start_time the same, only translate the 'text' field):\n"
                f"{json.dumps(voiceovers_for_prompt)}"
            )
        }
    ]

    response = open_ai_client.chat.completions.create(
        model="gpt-5-mini",
        response_model=TranslatedVoiceovers,
        messages=messages
    )

    translated_voiceovers_pre = response.model_dump()["voiceovers"]
    logger.debug("Translated voiceovers (before correction): %s", translated_voiceovers_pre)

    messages_2 = [
        {
            "role": "system",
            "content": (
                f"You are perfect in correcting speech errors and making sure that the text sounds natural in {LANGUAGES[language_index]['name']}"
            )
        },
        {
            "role": "user",
            "content": (
                "Make sure that each voicoevers text is correctly typed, sounds natural etc.\n"
                "Here are the voiceovers you need to correct:\n"
                f"{json.dumps(translated_voiceovers_pre)}"

            )
        }
    ]

    response_2 = open_ai_client.chat.completions.create(
        model="gpt-5-mini",
        response_model=TranslatedVoiceovers,
        messages=messages_2
    )

    translated_voiceovers = response_2.model_dump()["voiceovers"]
    logger.debug("Translated voiceovers: %s", translated_voiceovers)

    logger.info("Splitting translated voiceovers into pause segments")
    for vo in translated_voiceovers:
        splitted = re.split('[,.]', vo["text"])
        splitted_shorter = []
        for part in splitted:
            final_parts = []
            def split_longer_parts_of_sentence(words: str) -> List[str]:
                nonlocal final_parts
                # if the segment is longer than 8 words - split them apart
                # and if splitted part include more than 8 words - split again recursively
                words_list = words.split()
                if len(words_list) < 8:
                    final_parts.append(words.strip())
                else:
                    middle_index = len(words_list) // 2
                    splitted_first_part = ' '.join(words_list[:middle_index])
                    remaining_part = ' '.join(words_list[middle_index:])
                    split_longer_parts_of_sentence(splitted_first_part)
                    split_longer_parts_of_sentence(remaining_part)
            
            split_longer_parts_of_sentence(part)
            splitted_shorter.append("|".join(final_parts))
        
        content_with_pauses = "|".join(splitted_shorter)
        if content_with_pauses.endswith("|"):
            content_with_pauses = content_with_pauses[:-1]

        vo["text_with_pauses"] = content_with_pauses

    logger.debug("Voiceovers split with pauses: %s", json.dumps(translated_voiceovers))

    # for eahc voiceover we need to generate speech

    for vo in translated_voiceovers:
        filename = filename_from_name(f"voiceover_{uuid.uuid4()}")
        audio_path, duration, timestamps = generate_speech(
            text=vo["text"],
            filename=filename,
            directory="static/voiceovers",
            voice_id=LANGUAGES[language_index]["voice_id"]
        )
        vo["timestamps"] = json.dumps(timestamps)
        vo["src"] = audio_path
        vo["duration"] = duration
    
    logger.debug("Voiceovers after speech generation: %s", json.dumps(translated_voiceovers))

    return translated_voiceovers




        


