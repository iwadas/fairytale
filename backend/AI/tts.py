import json
from typing import Any
import requests
from dotenv import load_dotenv
import os
import time
from pydub import AudioSegment
from groq import Groq
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)


VOICEOVER_DIR = os.path.join(project_root, "static", "voiceovers")

load_dotenv()

class TTS:
    def __init__(self, provider: str="camb", text: str=None, voiceover_id: Any=None, project_id: str=None, **kwargs):
        """
        Docstring for __init__
        :param self: Description
        :param provider: Description
        :type provider: str
        :param text: Description
        :type text: str
        :param voiceover_id: Description
        :type voiceover_id: Any
        :param kwargs: language, voice_model_id, gender, age 
        """
        self.provider = provider
        self.text = text
        self.voiceover_id = voiceover_id
        self.project_id = project_id

        # VOICE SETTINGS
        self.voice_model_id = kwargs.get("voice_model_id", None)
        self.gender = kwargs.get("gender", 2)
        self.age = kwargs.get("age", None)
        self.language = kwargs.get("language", "english")

        # State
        self.api_key = None
        self.time = None
        self.duration = None
        self.timestamps = None
        self.src = None
        self.set_api_key()
        return self.generate()


    # HELPER METHODS
    def set_api_key(self):
        if self.provider == "camb":
            self.api_key = os.getenv("CAMB_AI_API_KEY")
            if not self.api_key:
                raise ValueError("CAMB_AI_API_KEY not found in environment variables.")
        else:
            raise ValueError(f"Unsupported TTS provider: {self.provider}")

    @staticmethod
    def gender_to_int(gender: str) -> int:
        if gender.lower() == "male":
            return 1
        elif gender.lower() == "female":
            return 2
        else:
            return 0
        
    @staticmethod
    def language_to_int(language: str) -> int:
        language_mapping = {
            "english": 1,
        }
        return language_mapping.get(language.lower(), 1)  

    @staticmethod
    def get_audio_duration(audio_file_path: str) -> float:
        try:
            audio = AudioSegment.from_file(audio_file_path)
            return len(audio) / 1000.0
        except Exception as e:
            print(f"Error getting duration: {e}")
            return 0.0
        
    @staticmethod
    def normalize_word(word: str) -> str:
        # Remove all punctuation (:,.;!? etc.) from the front and back of the word
        return word.strip('''.,!?;:"()[]{}<>''')

    def add_timestamps_to_audio(self, audio_file_path: str):
        """
        Perform STT with timestamps using Groq's API and store the timestamps in self.timestamps.
        """
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            print("GROQ_API_KEY missing, skipping timestamps.")
            return

        client = Groq(api_key=groq_api_key)

        try:
            with open(audio_file_path, "rb") as file:
                transcription = client.audio.transcriptions.create(
                file=(os.path.basename(audio_file_path), file.read()),
                model="whisper-large-v3-turbo",
                temperature=0,
                response_format="verbose_json",
                timestamp_granularities=["word"],
            )
            
            print(f"Transcription completed with timestamps for {audio_file_path}")
            print(f"Transcription text: {transcription}")

            self.timestamps = [
                {
                    "word": word_info["word"],
                    "start": word_info["start"],
                    "end": word_info["end"]
                }
                for word_info in transcription.words
            ]
        except Exception as e:
            print(f"Error adding timestamps to audio: {e}")
            self.timestamps = None


    # GENERATION METHODS
    def generate(self):
        if self.provider == "camb":
            self.generate_camb()
            self.add_timestamps_to_audio(self.src)
        else:
            return None
        
        return {
            "src": self.src,
            "duration": self.duration,
            "text": self.text,
            "id": self.voiceover_id,
            "project_id": self.project_id,
            "timestamps": json.dumps(self.timestamps),
            # FOR NOW EASY WAY
            "text_with_pauses": self.text,
        }

    # camb
    def generate_camb(self):
        try:
            tts_payload = {
                "text": self.text,
                "voice_id": self.voice_model_id,
                "language": self.language_to_int(self.language),
                "gender": self.gender_to_int(self.gender),
                "age": self.age
            }

            # Set up your API credentials
            headers = {
                "x-api-key": self.api_key,  # Replace with your actual API key
                "Content-Type": "application/json"
            }

            # Step 1: Submit your text-to-speech request
            response = requests.post(
                "https://client.camb.ai/apis/tts",
                json=tts_payload,
                headers=headers
            )

            # Check if the request was successful
            response.raise_for_status()
            task_data = response.json()
            task_id = task_data["task_id"]
            print(f"Speech task created! Task ID: {task_id}")

            # Step 2: Check progress until complete
            while True:
                status_response = requests.get(
                    f"https://client.camb.ai/apis/tts/{task_id}",
                    headers=headers
                )
                status_data = status_response.json()
                status = status_data["status"]
                print(f"Status: {status}")

                if status == "SUCCESS":
                    run_id = status_data["run_id"]
                    break
                elif status == "FAILED":
                    print("Task failed!")
                    break

                # Wait before checking again
                time.sleep(2)

            # Step 3: Download your audio file
            if status == "SUCCESS":
                print(f"Speech ready! Run ID: {run_id}")
                audio_response = requests.get(
                    f"https://client.camb.ai/apis/tts-result/{run_id}",
                    headers=headers,
                    stream=True
                )

                # Save the audio file
                os.makedirs(VOICEOVER_DIR, exist_ok=True)
                audio_file_path = os.path.join(VOICEOVER_DIR, f"{self.voiceover_id}.wav")
                with open(audio_file_path, "wb") as audio_file:
                    for chunk in audio_response.iter_content(chunk_size=1024):
                        if chunk:
                            audio_file.write(chunk)

                print(f"✨ Generated speech was saved as '{audio_file_path}'")
                # set duration of the audio file in seconds
                self.duration = self.get_audio_duration(audio_file_path)
                self.src = audio_file_path
        except Exception as e:
            print(f"Error generating TTS with camb: {e}")
    
# TESTING
if __name__ == "__main__":
    print("🚀 Starting TTS Debug...")

    # 1. Initialize the class
    tts_result = TTS(
        provider="camb",
        text="Hello, this is a test of the Camb TTS API.",
        voiceover_id="test_voiceover_1",
        voice_model_id=158880,
        language="english",
        gender="female",
    )


    # 3. Print the results to the console
    if tts_result:
        print("\n✅ Generation Successful!")
        print("-" * 30)
        print(f"📁 File Path:  {tts_result.get('src')}")
        print(f"⏱️ Duration:   {tts_result.get('duration')} seconds")
        print(f"🆔 Voice ID:   {tts_result.get('id')}")
        
        # Print first 8 timestamps to verify Groq worked
        timestamps = tts_result.get('timestamps')
        if timestamps:
            print(f"📝 Timestamps (First 8): {timestamps[:8]}")
        else:
            print("⚠️ No timestamps generated (Check Groq API Key)")
    else:
        print("\n❌ Generation Failed.")
    
 
        