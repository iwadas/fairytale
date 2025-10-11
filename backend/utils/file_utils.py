from google.genai import types
from pathlib import Path
import base64

def file_to_part(file_obj, mime="image/png") -> types.Part:
    if hasattr(file_obj, "file"):
        data = file_obj.file.read()
    elif hasattr(file_obj, "read"):
        data = file_obj.read()
    elif isinstance(file_obj, (str, Path)):
        with open(file_obj, "rb") as f:
            data = f.read()
    else:
        raise TypeError(f"Unsupported file type: {type(file_obj)}")
    return types.Part(
        inline_data=types.Blob(
            mime_type=mime,
            data=base64.b64encode(data).decode("utf-8"),
        )
    )