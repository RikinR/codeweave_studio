from __future__ import annotations

import os

from dotenv import load_dotenv
from groq import Groq


class GroqChatModel:
    DEFAULT_MODEL = "llama-3.3-70b-versatile"

    def __init__(
        self,
        *,
        temperature: float = 0,
        max_tokens: int = 4096,
        json_mode: bool = True,
    ):
        load_dotenv()
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in .env file")
        self.client = Groq(api_key=api_key)
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.json_mode = json_mode

    def invoke(self, messages: list[dict]):
        kwargs: dict = {
            "model": self.DEFAULT_MODEL,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if self.json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        return self.client.chat.completions.create(**kwargs)
