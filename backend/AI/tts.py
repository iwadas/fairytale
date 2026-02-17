import uuid
from dotenv import load_dotenv
import os
from pydub import AudioSegment
from groq import AsyncGroq
import sys
import aiofiles
import aiohttp
import asyncio

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
        if self.provider == "camb":
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

    async def generate(self, **kwargs):
        self.text = kwargs.get("text")
        if not self.text:
            raise ValueError("Text is required for TTS generation.")
        
        if self.provider == "camb":
            success = await self.generate_camb(**kwargs)
            if success and self.src:
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

    async def generate_camb(self, **kwargs):
        
        language = kwargs.get("language", "english")
        gender = kwargs.get("gender", "female")
        voice_model_id = kwargs.get("voice_model_id", "1")
        age = kwargs.get("age", 35)

        tts_payload = {
            "text": self.text,
            "voice_id": int(voice_model_id) if str(voice_model_id).isdigit() else 1,
            "language": self.language_to_int(language),
            "gender": self.gender_to_int(gender),
            "age": age
        }

        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }

        try:
            async with aiohttp.ClientSession() as session:
                # 1. Submit Request
                async with session.post(
                    "https://api.camb.ai/apis/tts",
                    json=tts_payload,
                    headers=headers
                ) as response:
                    response.raise_for_status()
                    task_data = await response.json()
                
                task_id = task_data.get("task_id")
                if not task_id:
                    print("No task_id received from Camb.ai")
                    return False

                print(f"Speech task created! Task ID: {task_id}")

                # 2. Polling
                run_id = None
                max_retries = 30
                attempts = 0

                while attempts < max_retries:
                    async with session.get(
                        f"https://api.camb.ai/apis/tts/{task_id}",
                        headers=headers
                    ) as status_response:
                        if status_response.status != 200:
                            print(f"Polling error: {status_response.status}")
                            await asyncio.sleep(2) # Async sleep
                            attempts += 1
                            continue

                        status_data = await status_response.json()
                        status = status_data.get("status")
                        print(f"Status: {status}")

                        if status == "SUCCESS":
                            run_id = status_data.get("run_id")
                            break
                        elif status == "FAILED":
                            print("Task failed at provider level.")
                            return False
                    
                    await asyncio.sleep(2) # Async sleep
                    attempts += 1
                
                if not run_id:
                    print("Timed out waiting for TTS generation.")
                    return False

                # 3. Download
                print(f"Speech ready! Run ID: {run_id}")
                
                output_dir = os.getenv("VOICEOVER_DIR", "voiceovers")
                os.makedirs(output_dir, exist_ok=True)
                audio_file_path = os.path.join(output_dir, f"{uuid.uuid4()}.wav")

                # Stream download using aiohttp and write using aiofiles
                async with session.get(
                    f"https://api.camb.ai/apis/tts-result/{run_id}",
                    headers=headers
                ) as audio_response:
                    audio_response.raise_for_status()
                    async with aiofiles.open(audio_file_path, "wb") as audio_file:
                        async for chunk in audio_response.content.iter_chunked(1024):
                            await audio_file.write(chunk)

            print(f"✨ Generated speech saved as '{audio_file_path}'")
            
            self.src = audio_file_path
            # Calculate duration asynchronously
            self.duration = await asyncio.to_thread(self.get_audio_duration, audio_file_path)
            return True

        except Exception as e:
            print(f"Error generating TTS with camb: {e}")
            return False