class LLM:
    def __init__(self, provider: str="xai", text=None, **kwargs):
        """
        Docstring for __init__
        
        :param self: Description
        :param provider: Description
        :type provider: str
        :param text: Description
        :param kwargs: Description
        """
        
        self.provider = provider
        self.api_key = None
        self.text = text
        self.resopnse_format = kwargs.get("response_format", "text")
        self.set_api_key()

    def set_api_key(self):
        if self.provider == "xai":
            self.api_key = os.getenv("XAI_API_KEY")
            if not self.api_key:
                raise ValueError("XAI_API_KEY not found in environment variables.")
        elif self.provider == "genai":
            self.api_key = os.getenv("GENAI_API_KEY")
            if not self.api_key:
                raise ValueError("GENAI_API_KEY not found in environment variables.")
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")