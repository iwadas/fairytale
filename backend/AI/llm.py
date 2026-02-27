from typing import Any
from openai import AsyncOpenAI
import instructor 

from database.crud import get_settings_db


class LLM:
    def __init__(self) -> "LLM":
        """
        Docstring for __init__
        :param self: Description
        :param provider: Description
        :type provider: str
        """
        self.provider = None
        self.client = None
        self.provider_settings = None

    @classmethod
    async def create(cls):
        instance = cls()
        await instance.provide_settings()
        return instance
    
    async def provide_settings(self):
        
        settings = await get_settings_db()
        if not settings:
            raise ValueError("Settings not found in database.")
        
        provider = settings.get("selected_llm_provider", None)
        if not provider:
            raise ValueError("LLM provider not selected in settings.")
        self.provider = provider

        llm_provider_settings = settings.get("llm_provider_settings", None)
        if not llm_provider_settings:
            raise ValueError("LLM provider settings not found in settings.")
        
        provider_settings = llm_provider_settings.get(self.provider, None)
        if not provider_settings:
            raise ValueError(f"Settings for selected LLM provider '{self.provider}' not found.")
       
        self.provider_settings = provider_settings

        api_key = provider_settings.get("api_key", None)
        if not api_key:
            raise ValueError(f"API key for provider '{self.provider}' not found in settings.")

        self.set_client(api_key=api_key)


    def set_client(self, api_key: str=None):
        if not self.provider or not api_key:
            raise ValueError("Provider and API key must be set to initialize LLM client.")

        if self.provider == "xai":
            self.client = instructor.from_openai(AsyncOpenAI(api_key=api_key, base_url="https://api.x.ai/v1"))
        elif self.provider == "openai":
            self.client = instructor.from_openai(AsyncOpenAI(api_key=api_key))
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    

    async def generate(self, messages: Any=None, response_format: Any=None):
        if not self.client:
            raise ValueError("LLM client not initialized.")
        
        if self.provider == "xai":
            return await self.generate_xai(messages=messages, response_format=response_format)
        elif self.provider == "openai":
            return await self.generate_openai(messages=messages, response_format=response_format)
        else:
            return None
        
    async def generate_xai(self, messages: Any=None, response_format: Any=None):
        

        ai_model = self.provider_settings.get("ai_model", None)
        if not ai_model:
            raise ValueError("AI model not specified in provider settings.")
        
        print("SENDING REQUEST TO XAI:")
        print("="*20)
        print("Messages:")
        for msg in messages:
            print(f"{msg['role']}: {msg['content']}")
        print("="*20)

        response = await self.client.chat.completions.create(
            model=ai_model,
            messages=messages,
            response_model=response_format,
        )
        print("GOT RESPONSE FROM XAI:")
        print("="*20)
        print(response)
        print("="*20)
        return response
    
    async def generate_openai(self, messages: Any=None, response_format: Any=None):
        return await self.generate_xai(messages=messages, response_format=response_format)
        