"""
Zhipu AI (GLM) Provider

API Documentation: https://open.bigmodel.cn/dev/api
Free Tier: 128K tokens/day with GLM-4-flash
"""
import os
from typing import List, Optional, AsyncGenerator
from openai import OpenAI

class ZhipuAIProvider:
    """
    Zhipu AI provider using OpenAI-compatible API.

    Zhipu AI offers GLM-4 series models optimized for Chinese language tasks.
    Free tier provides 128K tokens/day with GLM-4-flash.
    """

    def __init__(self):
        self.api_key = os.getenv("ZHIPU_API_KEY", "")
        self.base_url = "https://open.bigmodel.cn/api/paas/v4"
        self.chat_model = os.getenv("ZHIPU_CHAT_MODEL", "glm-4-flash")
        self.embedding_model = os.getenv("ZHIPU_EMBEDDING_MODEL", "embedding-2")

        # Use OpenAI-compatible client when credentials are configured.
        self.client = None
        if self.api_key:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )

        print(f"[Zhipu] Initialized: model={self.chat_model}, embedding={self.embedding_model}, key_length={len(self.api_key)}")

    async def chat(
        self,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 1500
    ) -> str:
        """
        Non-streaming chat completion.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens in response

        Returns:
            Generated response text
        """
        if self.client is None:
            raise ValueError("ZHIPU_API_KEY is not configured")

        try:
            response = self.client.chat.completions.create(
                model=self.chat_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[Zhipu] Chat error: {type(e).__name__}: {e}")
            raise

    async def chat_stream(
        self,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 1500
    ) -> AsyncGenerator[str, None]:
        """
        Streaming chat completion.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens in response

        Yields:
            Streamed response text chunks
        """
        if self.client is None:
            raise ValueError("ZHIPU_API_KEY is not configured")

        try:
            stream = self.client.chat.completions.create(
                model=self.chat_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            print(f"[Zhipu] Stream error: {type(e).__name__}: {e}")
            raise

    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Get text embedding vector.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats, or None if error
        """
        if self.client is None:
            print("[Zhipu] ZHIPU_API_KEY is not configured")
            return None

        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=text[:8000]  # Limit input length
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"[Zhipu] Embedding error: {type(e).__name__}: {e}")
            return None

    def is_configured(self) -> bool:
        """Check if Zhipu AI is properly configured."""
        return bool(self.api_key) and len(self.api_key) > 10

    def get_model_info(self) -> dict:
        """Get model configuration information."""
        return {
            "provider": "zhipu",
            "chat_model": self.chat_model,
            "embedding_model": self.embedding_model,
            "base_url": self.base_url,
            "configured": self.is_configured()
        }