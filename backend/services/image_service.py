from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import base64
import os
from app.config import settings
from app.utils.file_utils import file_to_part

def generate_image(directory: str, filename: str, prompt: str, content_images: dict = {}):
    contents = []
    for name, upload_file in content_images.items():
        contents.append(f"This is {name}:")
        contents.append(file_to_part(upload_file))
    contents.append(prompt)

    client = genai.Client(api_key=settings.genai_api_key)
    response = client.models.generate_content(
        model="gemini-2.5-flash-image-preview",
        contents=contents,
    )

    os.makedirs(directory, exist_ok=True)
    output_path = os.path.join(directory, f"{filename}.png")
    for part in response.candidates[0].content.parts:
        if part.inline_data:
            image = Image.open(BytesIO(part.inline_data.data))
            image.save(output_path)
    return output_path