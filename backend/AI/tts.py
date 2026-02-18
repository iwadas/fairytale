import uuid
from dotenv import load_dotenv
import os
from pydub import AudioSegment
import sys
import aiofiles
import asyncio
import mimetypes
import wave

from typing import Callable, Optional

from groq import AsyncGroq
from camb.client import AsyncCambAI, save_async_stream_to_file
from camb.types.stream_tts_output_configuration import StreamTtsOutputConfiguration
from google import genai
from google.genai import types

# Standard path setup
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

load_dotenv()

class TTS:
    def __init__(self, provider: str = "camb"):
        self.provider = provider
        self.api_key = None
        self.duration = 0.0
        self.timestamps = []
        self.src = None
        self.text = None

        self.set_api_key()

    def set_api_key(self):
        if self.provider == "gemini":
            self.api_key = os.getenv("GENAI_API_KEY")
            if not self.api_key:
                raise ValueError("GENAI_API_KEY not found in environment variables.")
        elif self.provider == "camb":
            self.api_key = os.getenv("CAMB_AI_API_KEY")
            if not self.api_key:
                raise ValueError("CAMB_AI_API_KEY not found in environment variables.")
        else:
            raise ValueError(f"Unsupported TTS provider: {self.provider}")

    @staticmethod
    def gender_to_int(gender: str) -> int:
        gender = gender.lower()
        if gender == "male":
            return 1
        elif gender == "female":
            return 2
        return 0
        
    @staticmethod
    def language_to_int(language: str) -> int:
        # Extend this mapping based on Camb.ai documentation
        language_mapping = {
            "english": 1,
            # Add other languages here if needed
        }
        return language_mapping.get(language.lower(), 1) 
    
    @staticmethod
    def language_to_code(language: str) -> str:
        language = language.lower()
        if language == "english":
            return "en-us"
        # Extend this mapping based on Camb.ai documentation
        return "en-us"  # Default to English if unknown

    @staticmethod
    def get_audio_duration(audio_file_path: str) -> float:
        if not os.path.exists(audio_file_path):
            return 0.0
        try:
            audio = AudioSegment.from_file(audio_file_path)
            return len(audio) / 1000.0
        except Exception as e:
            print(f"Error calculating duration: {e}")
            return 0.0

    async def add_timestamps_to_audio(self, audio_file_path: str):
        """
        Perform STT with timestamps using Groq's API.
        """

        print("Starting TTS generation with Camb.ai...")


        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            print("GROQ_API_KEY missing, skipping timestamps.")
            return

        client = AsyncGroq(api_key=groq_api_key)

        try:

            async with aiofiles.open(audio_file_path, "rb") as f:
                file_content = await f.read()

            transcription = await client.audio.transcriptions.create(
                file=(os.path.basename(audio_file_path), file_content),
                model="whisper-large-v3-turbo",
                temperature=0,
                response_format="verbose_json",
                timestamp_granularities=["word"],
            )
            
     
            if hasattr(transcription, 'words'):
                self.timestamps = []
                for word_obj in transcription.words:
                    if isinstance(word_obj, dict):
                        self.timestamps.append({
                            "word": word_obj.get("word"),
                            "start": word_obj.get("start"),
                            "end": word_obj.get("end")
                        })
                    else:
                        self.timestamps.append({
                            "word": word_obj.word,
                            "start": word_obj.start,
                            "end": word_obj.end
                        })
            else:
                print("No word-level timestamps returned from Groq.")

        except Exception as e:
            print(f"Error adding timestamps to audio: {e}")
            self.timestamps = []

    async def generate(self, progress_callback: Optional[Callable] = None, **kwargs):
        self.text = kwargs.get("text")

        if not self.text:
            raise ValueError("Text is required for TTS generation.")
        
        if progress_callback:
            await progress_callback(
                status="in_progress", 
                message="⌨️ Generatating voiceover for text: " + (self.text[:50] + "..." if len(self.text) > 50 else self.text)
            )

        if self.provider == "gemini":
            success = await self.generate_gemini(**kwargs)
            if success and self.src:
                if progress_callback:
                    await progress_callback(
                        status="in_progress", 
                        message="⌨️ Adding timestamps to generated voiceover..."
                    )

                await self.add_timestamps_to_audio(self.src)

        elif self.provider == "camb":
            success = await self.generate_camb(**kwargs)
            if success and self.src:
                if progress_callback:
                    await progress_callback(
                        status="in_progress", 
                        message="⌨️ Adding timestamps to generated voiceover..."
                    )

                await self.add_timestamps_to_audio(self.src)
            else:
                return None
        else:
            return None
        
        return {
            "src": self.src,
            "duration": self.duration,
            "text": self.text,
            "timestamps": self.timestamps, # Return list directly, let caller jsonify if needed
            "text_with_pauses": self.text,
        }


    async def generate_gemini(self, **kwargs):
        model = "gemini-2.5-flash-preview-tts"
        voice_name = kwargs.get("voice_name", "Algenib")

        voice_style = kwargs.get("voice_style", "Read aloud in a deep, warm and stoic tone, fast paced:")
        self.text = kwargs.get("text", None)

        output_file = f"{uuid.uuid4()}.wav"
        output_dir = os.getenv("VOICEOVER_DIR", "voiceovers")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, output_file)

        contents = f"{voice_style} {self.text}"
        
        generate_content_config = types.GenerateContentConfig(
            temperature=1,
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voice_name
                    )
                )
            ),
        )

        client = genai.Client(
            api_key=self.api_key
        )

        try:
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=model,
                contents=contents,
                config=generate_content_config
            )
        except Exception as e:
            print(f"Gemini API Error: {e}")
            return False

        def save_audio_file(filename, pcm, channels=1, rate=24000, sample_width=2):
            with wave.open(filename, "wb") as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(sample_width)
                wf.setframerate(rate)
                wf.writeframes(pcm)

        if response.candidates and response.candidates[0].content.parts:
            data = response.candidates[0].content.parts[0].inline_data.data
            await asyncio.to_thread(save_audio_file, output_path, data)

            self.src = output_path
            self.duration = await asyncio.to_thread(self.get_audio_duration, output_path)
            
            return True
        
        return False


    async def generate_camb(self, **kwargs):
        print("Starting TTS generation with Camb.ai SDK...")

        # Initialize the Async Client
        client = AsyncCambAI(api_key=self.api_key)

        # Parse arguments
        raw_language = kwargs.get("language", "english")
        language_code = self.language_to_code(raw_language)
        
        # Ensure voice_id is an integer
        voice_model_id = kwargs.get("voice_model_id", 1)
        try:
            voice_id = int(voice_model_id)
        except (ValueError, TypeError):
            voice_id = 1
        
        # Output setup
        output_dir = os.getenv("VOICEOVER_DIR", "voiceovers")
        os.makedirs(output_dir, exist_ok=True)
        filename = f"{uuid.uuid4()}.mp3"
        audio_file_path = os.path.join(output_dir, filename)

        try:
            # Call the TTS endpoint (Stream)
            response = client.text_to_speech.tts(
                text=self.text,
                language=language_code,
                voice_id=voice_id,
                speech_model="mars-pro", # Use 'mars-pro' if you need higher quality over speed
                output_configuration=StreamTtsOutputConfiguration(
                    format="mp3"
                )
            )

            # Stream to file using SDK utility
            await save_async_stream_to_file(response, audio_file_path)

            print(f"✨ Generated speech saved as '{audio_file_path}'")
            
            self.src = audio_file_path
            
            # Calculate duration asynchronously
            self.duration = await asyncio.to_thread(self.get_audio_duration, audio_file_path)
            return True

        except Exception as e:
            print(f"Error generating TTS with camb SDK: {e}")
            return False