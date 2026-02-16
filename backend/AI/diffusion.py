import string
import time
import mimetypes
from typing import Optional
import uuid
import json
import os
from pathlib import Path
import base64
import aiohttp


from fastapi import HTTPException
from dotenv import load_dotenv


from runware import Runware, IVideoInference, IFrameImage, IBytedanceProviderSettings


OUTPUT_DIR = Path("static/videos/scenes")
MAX_ATTEMPTS = 100
POLL_INTERVAL = 5

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

    def set_client(self):
        if self.provider == "runware":
            self.api_key = os.getenv("RUNWARE_API_KEY")
            if not self.api_key:
                raise ValueError("RUNWARE_API_KEY not found in environment variables.")
            

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
    def normalize_filename( name: str) -> str:
        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        normalized = ''.join(c for c in name if c in valid_chars)
        normalized = normalized.replace(' ', '_')
        return normalized[:50]
    
    @staticmethod
    def get_frames_runware(self, frames: list) -> list:
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
            "middle": "middle",
            "end": "last"
        }

        prepared_frames = []
        for frame in frames:
            if not os.path.exists(frame["src"]):
                raise ValueError(f'Image path not found: {frame["src"]}')
            
            image_data_uri = self.encode_image_to_base64(frame["src"])
            print("Including image in payload")
            if(len(frames) == 1):
                frame_image = IFrameImage(inputImage=image_data_uri)
            else:
                frame_image = IFrameImage(inputImage=image_data_uri, frame=DB_TO_RUNWARE_FRAME_MAPPING[frame["time"]]) 
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
                with open(output_path, "wb") as f:
                    while True:
                        chunk = await response.content.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)


    # CORE
    async def generate(self, prompt: str=None, frames: Optional[list]=None, duration: Optional[int]=3, filename: Optional[str]=None):
        if self.provider == "runware":
            return await self.generate_runware(prompt=prompt, frames=frames, duration=duration, filename=filename)


    async def generate_runware(self, prompt: str=None, frames: Optional[list]=None, duration: Optional[int]=3, filename: Optional[str]=None):


        if not self.api_key:
            raise ValueError("Runway API key not set.")
        if not prompt:
            raise ValueError("Prompt is required for video generation.")

        os.makedirs(OUTPUT_DIR, exist_ok=True)

        filename = self.normalize_filename(filename) if filename else str(uuid.uuid4())
        output_path = os.path.join(OUTPUT_DIR, f"{filename}.mp4") if filename else os.path.join(OUTPUT_DIR, f"{str(uuid.uuid4())}.mp4")

        runware = Runware(api_key=self.api_key)

        try:
            await runware.connect()

            request = IVideoInference(
                positivePrompt=prompt,
                model=self.diffusion_model if self.diffusion_model else "bytedance:1@1",
                width=self.resolution[0],
                height=self.resolution[1],
                fps=self.fps,
                duration=duration,
                numberResults=1,
                frameImages=self.get_frames_runware(frames) if frames else [],
                # providerSettings=IBytedanceProviderSettings(cameraFixed=False)
            )

            videos = await runware.videoInference(requestVideo=request)
            # 1 videos is expected
            if not videos or len(videos) == 0:
                raise ValueError("No video generated by Runware.")
            await self.download_mp4_from_url(videos[0].videoURL, output_path)
            return output_path
        except Exception as e:
            print(f"Error during Runware video generation: {e}")
            raise HTTPException(status_code=500, detail=f"Video generation failed: {str(e)}")
        finally:
            await runware.disconnect()