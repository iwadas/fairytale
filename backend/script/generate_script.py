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
        else:
            context_instruction = ""

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
          
                f"{f'Context: {self.description}\\n\\n' if self.description else ''}"
                f"{context_instruction}"

                "**Structure:**\n"
                "1. Hook (0-3s): Relatable 'Did you know?', psychological framing ('According to psychology...'), or a highly specific everyday scenario. No 'Hello'.\n"
                "2. Mechanism: How it works (explain the 'why' using conversational authority).\n"
                "3. The Twist/Deep Reason: The emotional core of why this happens or why it matters.\n"
                "4. Call to Action: Organic, one-sentence closing (e.g., 'If this made sense to you, comment true.' or 'Send this to that one friend they deserve to know.'). No marketing speak.\n\n"
                "**Style:**\n"
                "- No fluff.\n"
                "- Conversational Authority: Use one or two scientific/psychological terms but explain them plainly, like a smart friend sitting on a couch.\n"
                "- STRICTLY NO flowery, poetic, aggressive, or dystopian metaphors. Keep it grounded in literal, lived reality.\n"
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
            "content": "You are a Psychological Storyteller. Your job is to enhance hypnotic flow, use deeply validating language, and make the viewer feel seen and understood."
        }
        
        user_message = {
            "role": "user",
            "content": (
                f"Here is a draft script:\n\"\"\"{raw_script}\"\"\"\n\n"
                "**Critically analyze this draft and rewrite it to increase retention and emotional resonance:**\n"
                "1. **Lived Experiences (NO LISTS):** Pick ONE strong, specific visual per idea. Do NOT cram multiple examples into a sentence. Let one relatable scenario breathe (e.g., just say 'a delayed text', don't add 5 more examples next to it).\n"
                "2. **Compression:** Cut the word count by around 10% without losing information.\n"
                "3. **Hypnotic Rhythm (NO STACKING):** Vary sentence length drastically, but NEVER stack short sentences together (e.g., absolutely no 'Breathe. Observe. Share.'). Build tension with a longer, winding sentence, then deliver exactly ONE profound 2-5 word realization per paragraph (e.g., 'That's trust.').\n"
                "4. **Validating Tone:** Ensure the script acts as a comforting guide. Absolve the viewer of guilt by explaining their behaviors or feelings as natural, human, or biologically hardwired (e.g., 'You're not weak... you're human', 'It's an evolutionary glitch').\n"
                "5. **Organic CTA:** The final sentence must be a seamless, viral-style invitation (e.g., 'If this changed how you see it, comment true.'). Do not use overly eager phrases like 'Share below' or 'We are in this together'.\n"
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
                "1. Insert <br> tags for every part that introduces a new idea (every 2-4 sentences) to create natural pauses.\n"
                "2. Return raw text only.\n"
                "3. Do NOT add <br> inside a fast-paced or tightly connected sentence.\n"
            )
        }
        
        class FormattedScriptResponse(BaseModel):
            formatted_script: str

        response = await self.llm_client.generate(
            messages=[role_message, user_message],
            response_format=FormattedScriptResponse
        )

        return response.formatted_script.strip().replace("\n", " ").replace("<br><br>", "<br>").replace("  ", " ")