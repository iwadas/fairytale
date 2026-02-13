from typing import Any
import os
from openai import OpenAI
import instructor 
from dotenv import load_dotenv

class LLM:
    def __init__(self, provider: str="xai", **kwargs) -> "LLM":
        """
        Docstring for __init__
        :param self: Description
        :param provider: Description
        :type provider: str
        """
        load_dotenv()
        self.provider = provider
        self.api_key = None
        self.ai_model = kwargs.get("ai_model", None)
        self.client = None
        self.set_client()

    def set_client(self):
        if self.provider == "xai":
            self.api_key = os.getenv("XAI_API_KEY")
            if not self.api_key:
                raise ValueError("XAI_API_KEY not found in environment variables.")
            self.client = instructor.from_openai(OpenAI(api_key=self.api_key, base_url="https://api.x.ai/v1"))
        elif self.provider == "genai":
            self.api_key = os.getenv("GENAI_API_KEY")
            if not self.api_key:
                raise ValueError("GENAI_API_KEY not found in environment variables.")
            self.client = instructor.from_google_genai(api_key=self.api_key)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    

    def generate(self, messages: Any=None, response_format: Any=None):
        if not self.client:
            raise ValueError("LLM client not initialized.")
        
        if self.provider == "xai":
            return self.generate_xai(messages=messages, response_format=response_format)
        else:
            return None
        
    def generate_xai(self, messages: Any=None, response_format: Any=None):
        if not self.ai_model:
            raise ValueError("AI model not specified.")

        print("SENDING REQUEST TO XAI:")
        print("" + "="*20)
        print("Messages:")
        for msg in messages:
            print(f"{msg['role']}: {msg['content']}")
        print("" + "="*20)
        response = self.client.chat.completions.create(
            model=self.ai_model,
            messages=messages,
            response_model=response_format,
        )
        print("GOT RESPONSE FROM XAI:")
        print("" + "="*20)
        print(response)
        print("" + "="*20)
        return response
        