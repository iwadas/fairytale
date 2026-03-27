import string
from typing import Optional
import uuid
import os
from pathlib import Path
import base64

import aiohttp
from fastapi.concurrency import run_in_threadpool
import aiofiles

from fastapi import HTTPException
from dotenv import load_dotenv

from database.crud import get_settings_db
from runware import Runware, IVideoInference, IFrameImage, IVideoInputs, IBytedanceProviderSettings


class DictWrapper:
    def __init__(self, data_dict):
        self.data_dict = data_dict
        
    def to_request_dict(self):
        # When the SDK asks for the data, we hand it the raw dictionary
        return self.data_dict

class DynamicProviderSettings:
    def __init__(self, provider_name: str, settings: dict):
        self.provider_name = provider_name
        self.settings = settings
        
    def to_request_dict(self):
        # Outputs exactly what the API wants: {"klingai": {"sound": False}}
        return {self.provider_name: self.settings}

class Diffusion:
    def __init__(
        self, 
        provider: str="runware", 
        diffusion_model: str=None, 
        resolution: Optional[tuple]=(1024, 1024),
        fps: Optional[int]=24,
        **kwargs
    ) -> "Diffusion":
    
        """
        Docstring for __init__
        :param self: Description
        :param provider: Description
        :type provider: str
        """
        load_dotenv()
        self.provider = provider
        self.diffusion_model = diffusion_model
        self.resolution = resolution
        self.fps = fps
        self.api_key = None
        self.client = None
        self.set_client()


    @classmethod
    async def create(cls):
        instance = cls()
        await instance.provide_settings()
        return instance
    
    async def provide_settings(self):
        settings = await get_settings_db()

        print("Diffusion Settings:", settings)
        if not settings:
            raise ValueError("Settings not found in database.")
        if not settings.get("selected_diffusion_provider"):
            raise ValueError("No diffusion provider selected in settings.")
        self.provider = settings["selected_diffusion_provider"]
        diffusion_provider_settings = settings.get("diffusion_provider_settings", None)
        if not diffusion_provider_settings:
            raise ValueError("Diffusion provider settings not found in settings.")
        provider_settings = diffusion_provider_settings.get(self.provider, None)
        if not provider_settings:
            raise ValueError(f"Settings for selected diffusion provider '{self.provider}' not found.")
        self.provider_settings = provider_settings

        api_key = provider_settings.get("api_key")
        if not api_key:
            raise ValueError(f"API key for provider '{self.provider}' not found in settings.")
        
        self.api_key = api_key

        diffusion_model = provider_settings.get("diffusion_model")
        if not diffusion_model:
            raise ValueError(f"Diffusion model for provider '{self.provider}' not found in settings.")
        self.diffusion_model = diffusion_model

        resolution = provider_settings.get("resolution")
        if not resolution:
            raise ValueError(f"Resolution for provider '{self.provider}' not found in settings.")
        self.resolution = tuple(map(int, resolution.split('x')))

        self.set_client()


    def set_client(self):
        if self.provider == "runware":
            self.api_key = os.getenv("RUNWARE_API_KEY")
            if not self.api_key:
                raise ValueError("RUNWARE_API_KEY not found in environment variables.")
            self.client = Runware(api_key=self.api_key)
        else:
            raise ValueError(f"Unsupported diffusion provider: {self.provider}")

    # HELPERS
    @staticmethod
    def encode_image_to_base64(image_path):
        """Converts a local file to a base64 data URL."""
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found at {image_path}")
            
        with open(path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            ext = path.suffix.lower().replace(".", "")
            mime_type = f"image/{ext}" if ext != "jpg" else "image/jpeg"
            return f"data:{mime_type};base64,{encoded_string}"

    @staticmethod
    def normalize_filename(name: str) -> str:
        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        normalized = ''.join(c for c in name if c in valid_chars)
        normalized = normalized.replace(' ', '_')
        return normalized[:50]
    
    async def get_frames_runware(self, frames: list) -> list:
        """
        Prepares the frame images for the API by encoding them as base64 data URLs 
        and structuring them as raw dictionaries to bypass SDK serialization errors.
        """
        DB_TO_RUNWARE_FRAME_MAPPING = {
            "start": "first",
            "end": "last"
        }

        prepared_frames = []
        for frame in frames:
            if not os.path.exists(frame["src"]):
                raise ValueError(f'Image path not found: {frame["src"]}')
            
            image_data_uri = await run_in_threadpool(self.encode_image_to_base64, frame["src"])
            print("Including image in payload")
            
            # Build a raw dictionary instead of using the broken IFrameImage class
            if len(frames) == 1:
                frame_dict = {
                    "image": image_data_uri,
                    "frame": "first"  # Explicitly setting 'first' as the Kling API seems to expect it
                }
            else:
                runware_time = DB_TO_RUNWARE_FRAME_MAPPING.get(frame["time"], "first")
                frame_dict = {
                    "image": image_data_uri,
                    "frame": runware_time
                }
                
            prepared_frames.append(frame_dict)
        
        return prepared_frames

    async def get_frames_runware_old(self, frames: list) -> list:
        """
        Prepares the frame images for the Runware API by encoding them as base64 data URLs and structuring them according to the API's requirements.
        
        :param self: Description
        :param frames: Description
        :type frames: list
        :return: Description
        :rtype: list
        """

        DB_TO_RUNWARE_FRAME_MAPPING = {
            "start": "first",
            "end": "last"
        }

        prepared_frames = []
        for frame in frames:
            if not os.path.exists(frame["src"]):
                raise ValueError(f'Image path not found: {frame["src"]}')
            
            image_data_uri = await run_in_threadpool(self.encode_image_to_base64, frame["src"])
            print("Including image in payload")
            if(len(frames) == 1):
                frame_image = IFrameImage(inputImage=image_data_uri)
            else:
                runware_time = DB_TO_RUNWARE_FRAME_MAPPING.get(frame["time"], "first")
                frame_image = IFrameImage(inputImage=image_data_uri, frame=runware_time) 
            prepared_frames.append(frame_image)
        
        return prepared_frames
    
    @staticmethod
    async def download_mp4_from_url(url: str, output_path: str):
        """
        Downloads an MP4 video from a given URL and saves it to the specified output path.
        
        :param self: Description
        :param url: Description
        :type url: str
        :param output_path: Description
        :type output_path: str
        """
        timeout = aiohttp.ClientTimeout(total=300)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                response.raise_for_status()
                async with aiofiles.open(output_path, "wb") as f:
                    while True:
                        chunk = await response.content.read(8192)
                        if not chunk:
                            break
                        await f.write(chunk)

    # CORE
    async def generate(self, prompt: str=None, frames: Optional[list]=None, duration: Optional[int]=3, filename: Optional[str]=None):

        if self.provider == "runware":
            return await self.generate_runware(prompt=prompt, frames=frames, duration=duration, filename=filename)




    async def generate_runware(self, prompt: str=None, frames: Optional[list]=None, duration: Optional[int]=3, filename: Optional[str]=None):
        if not prompt:
            raise ValueError("Prompt is required for video generation.")
        elif not self.client:
            raise ValueError("Runware client not initialized.")


        output_dir = os.getenv("SCENE_VIDEO_DIR", "static/videos/scenes")
        os.makedirs(output_dir, exist_ok=True)

        filename = self.normalize_filename(filename) if filename else str(uuid.uuid4())
        output_path = os.path.join(output_dir, f"{filename}.mp4") if filename else os.path.join(output_dir, f"{str(uuid.uuid4())}.mp4")

        
        try:
            await self.client.connect()

            frames = await self.get_frames_runware_old(frames) if frames else None

            print("diffusion_model:", self.diffusion_model)

            # KLINGAI
            if "klingai" in self.diffusion_model.lower():
                request = IVideoInference(
                    positivePrompt=prompt,
                    model=self.diffusion_model,
                    # resolution=tuple(self.resolution),
                    # fps=self.fps,
                    duration=duration,
                    numberResults=1,
                    inputs=IVideoInputs(
                        frameImages=frames
                    ),
                    # providerSettings=IBytedanceProviderSettings(audio=False)
                    # providerSettings=IKlingAIProviderSettings(
                    #     sound=False
                    # )
                    providerSettings=DynamicProviderSettings("klingai", {"sound": False})
                )
            elif "seedance" in self.diffusion_model.lower():
                request = IVideoInference(
                    positivePrompt=prompt,
                    model=self.diffusion_model,
                    resolution='480p',
                    duration=duration,
                    numberResults=1,
                    frameImages=frames,
                    providerSettings=IBytedanceProviderSettings(audio=False)
                )

            task_response = await self.client.videoInference(requestVideo=request)
            task_uuid = task_response.taskUUID
            print(f"Video generation started. Task UUID: {task_uuid}")

            videos = await self.client.getResponse(
                taskUUID=task_uuid, 
                numberResults=1
            )

            print("\n--- DEBUG: RAW GETRESPONSE ---")
            print(f"Type of response: {type(videos)}")

            # If it returned a list, let's look inside the first item
            if isinstance(videos, list) and len(videos) > 0:
                print(f"Type of item 0: {type(videos[0])}")
                # vars() extracts all the attributes of the object so you can actually read them
                print(f"Contents of item 0: {vars(videos[0]) if hasattr(videos[0], '__dict__') else videos[0]}")
            else:
                # If it's not a list, just print whatever it is
                print(f"Contents: {vars(videos) if hasattr(videos, '__dict__') else videos}")
            print("------------------------------\n")

            # 1 videos is expected
            if not videos or len(videos) == 0:
                raise ValueError("No video generated by Runware.")
            await self.download_mp4_from_url(videos[0].videoURL, output_path)
            return output_path
        except Exception as e:
            print(f"Error during Runware video generation: {e}")
            raise HTTPException(status_code=500, detail=f"Video generation failed: {str(e)}")
        finally:
            await self.client.disconnect()