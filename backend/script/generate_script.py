from typing import Optional
from AI.llm import LLM
from pydantic import BaseModel
import asyncio

class ScriptGenerator:
    def __init__(   self, 
                    llm_client: LLM,
                    topic: str = None,
                    description: Optional[str] = None,
                    story_data: Optional[str] = None, 
                    reference_stories: Optional[str] = None,
                    persistant_characters: bool = False,
                    word_limit: int = 180,
                ):
        self.llm_client = llm_client
        self.topic = topic
        self.description = description
        self.story_data = story_data
        self.reference_stories = reference_stories
        self.persistant_characters = persistant_characters
        self.word_limit = word_limit

    async def generate(self) -> str:

        raw_script = await self.generate_script_raw()

        refined_script = await self.refine_script(raw_script)

        formatted_script = await self.format_script(refined_script)

        return formatted_script
    
    async def generate_script_raw(self) -> str:
        if self.story_data and self.reference_stories:
            context_instruction = (
                f"Base the story entirely on reference stories and gathered data:\n"
                f"Data:\n{self.story_data}\n\n"
                f"Example reference stories about the topic: \n{self.reference_stories}\n\n"
            )
        elif self.story_data:
            context_instruction = (
                f"Base the story entirely on the following gathered data about the topic:\n{self.story_data}\n\n"
            )
        elif self.reference_stories:
            context_instruction = (
                f"Base the story entirely on the following reference stories about the topic: \n{self.reference_stories}\n\n"
            )

        role_message = {
            "role": "system",
            "content": (
                "You are an expert scriptwriter for short-form video (TikTok/Reels)."
            )
        }

        user_message = {
            "role": "user",
            "content": (
                f"Write a {self.word_limit} word raw script about: {self.topic}\n"
          
                f"{f'Context: {self.description}\n\n' if self.description else ''}"
                f"{context_instruction if (self.story_data or self.reference_stories) else ''}"

                "**Structure:**\n"
                "1. Hook (0-3s): Direct challenge. No 'Hello'.\n"
                "2. Mechanism: How it works (Fast facts).\n"
                "3. The Twist/Deep Reason: Why it matters.\n\n"
                "**Style:**\n"
                # "- Fast-paced.\n"
                "- No fluff.\n"
                "- Use simple, sharp words.\n"
                "- Do NOT format the text yet. Just write the paragraphs."
            )
        }
        
        class ScriptResponse(BaseModel):
            script: str

        response = await self.llm_client.generate(
            messages=[role_message, user_message],
            response_format=ScriptResponse
        )

        return response.script.strip()
    
    async def refine_script(self, raw_script: str) -> str:
        
        role_message = {
            "role": "system",
            "content": "You are a Retention Editor. Your job is to delete boring parts and spike dopamine."
        }
        
        user_message = {
            "role": "user",
            "content": (
                f"Here is a draft script:\n\"\"\"{raw_script}\"\"\"\n\n"
                "**Critically analyze this draft and rewrite it to increase retention:**\n"
                "1. **Use sensory language:** Make the viewer see, feel, and hear the content. Instead of 'The brain releases dopamine', say 'The brain's reward center floods with dopamine, giving you that rush of pleasure'.\n"
                "2. **Compression:** Cut the word count by around 10% without losing information.\n"
                "3. **Rhythm:** Vary sentence length. One long sentence followed by a two-word sentence.\n"
                "\n\nReturn ONLY the improved script."
            )
        }
        
        class RefinedScriptResponse(BaseModel):
            refined_script: str

        response = await self.llm_client.generate(
            messages=[role_message, user_message],
            response_format=RefinedScriptResponse
        )

        return response.refined_script.strip()
    
    async def format_script(self, refined_script: str) -> str:
        
        role_message = {
            "role": "system",
            "content": "You are a TTS (Text-to-Speech) formatting engine."
        }
        
        user_message = {
            "role": "user",
            "content": (
                f"Format the following script for audio generation:\n\"\"\"{refined_script}\"\"\"\n\n"
                "**Rules:**\n"
                "1. Insert <br> tags, for every part that introduces new idea (every 2-4 sentences).\n"
                "2. Return raw text only."
                "3. Do NOT add <br> inside a fast-paced sentence.\n"
            )
        }
        
        class FormattedScriptResponse(BaseModel):
            formatted_script: str

        response = await self.llm_client.generate(
            messages=[role_message, user_message],
            response_format=FormattedScriptResponse
        )

        return response.formatted_script.strip().replace("\n", " ").replace("<br><br>", "<br>").replace("  ", " ")