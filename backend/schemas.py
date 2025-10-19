from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class CharacterShortInput(BaseModel):
    name: str
    short_description: str

class ProjectOutput(BaseModel):
    id: str  # UUID as string
    name: str
    scenes: List["SceneOutput"]
    characters: List["CharacterOutput"]
    voiceovers: List["VoiceoverOutput"]
    created_at: Optional[datetime]
    places: List["PlaceOutput"]

    class Config:
        from_attributes = True  # For Pydantic 2.x

class ProjectBasicOutput(BaseModel):
    id: str
    name: str
    created_at: Optional[datetime]

    class Config:
        from_attributes = True

class VoiceoverOutput(BaseModel):
    id: str  # UUID as string
    src: Optional[str]
    text: Optional[str]
    project_id: str
    start_time: float
    duration: Optional[float]

    class Config:
        from_attributes = True

class CharacterOutput(BaseModel):
    id: str  # UUID as string
    name: str
    prompt: Optional[str]  # Description for AI image generation
    src: Optional[str]

    class Config:
        from_attributes = True

class PlaceOutput(BaseModel):
    id: str  # UUID as string
    name: str
    prompt: str  # Description for AI image generation
    src: Optional[str]

    class Config:
        from_attributes = True

class SceneOutput(BaseModel):
    id: str  # UUID as string
    scene_number: int
    duration: Optional[int]  # <8 seconds
    image_prompt: Optional[str]  # Prompt for scene visuals, incorporating characters
    image_src: Optional[str]
    video_prompt: Optional[str]  # Prompt for scene video generation
    video_src: Optional[str]
    project_id: str
    characters: List[CharacterOutput]  # List of character IDs (UUID strings)
    places: List[PlaceOutput]

    class Config:
        from_attributes = True

class PromptRequest(BaseModel):
    prompt: str

class FixedPromptResponse(BaseModel):
    fixed_prompt: str

class ProjectIn(BaseModel):
    title: str  # Topic/story title
    style: str  # e.g., "epic fantasy", "noir thriller"
    voiceover_style: str  # e.g., "dramatic", "calm"
    prompt: str
    duration: int = 10  # Total film duration in seconds

class CharacterOut(BaseModel):
    id: str
    name: str
    prompt: str

class PlaceOut(BaseModel):
    id: str
    name: str
    prompt: str

class SceneOut(BaseModel):
    scene_number: int
    duration: int
    image_prompt: str
    video_prompt: str
    character_ids: List[str]
    places_ids: List[str]

class VoiceoverOut(BaseModel):
    id: str
    text: str
    start_time: int
    duration: int

class ProjectOut(BaseModel):
    characters: List[CharacterOut]
    scenes: List[SceneOut]
    voiceovers: List[VoiceoverOut]
    places: List[PlaceOut]
