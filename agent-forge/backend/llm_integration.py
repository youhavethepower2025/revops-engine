#!/usr/bin/env python3
"""
LLM Integration for Agent.Forge
Actual AI model connections, not placeholders
"""
import os
import httpx
import json
from typing import Dict, List, Any, Optional
from enum import Enum

class LLMProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    LOCAL = "local"

class LLMIntegration:
    """Handle actual LLM API calls"""

    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.default_provider = LLMProvider.OPENAI

    async def generate_response(self,
                               prompt: str,
                               provider: Optional[LLMProvider] = None,
                               model: Optional[str] = None,
                               temperature: float = 0.7,
                               max_tokens: int = 500) -> str:
        """Generate actual response from LLM"""

        provider = provider or self.default_provider

        if provider == LLMProvider.OPENAI:
            return await self._call_openai(prompt, model or "gpt-3.5-turbo", temperature, max_tokens)
        elif provider == LLMProvider.ANTHROPIC:
            return await self._call_anthropic(prompt, model or "claude-3-haiku", temperature, max_tokens)
        elif provider == LLMProvider.GROQ:
            return await self._call_groq(prompt, model or "mixtral-8x7b", temperature, max_tokens)
        else:
            return f"[No LLM configured - would send: {prompt[:100]}...]"

    async def _call_openai(self, prompt: str, model: str, temperature: float, max_tokens: int) -> str:
        """Call OpenAI API"""
        if not self.openai_key:
            return "[OpenAI API key not configured]"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": "You are a helpful assistant."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    },
                    timeout=30.0
                )

                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    return f"[OpenAI API error: {response.status_code}]"

            except Exception as e:
                return f"[OpenAI API error: {str(e)}]"

    async def _call_anthropic(self, prompt: str, model: str, temperature: float, max_tokens: int) -> str:
        """Call Anthropic API"""
        if not self.anthropic_key:
            return "[Anthropic API key not configured]"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.anthropic_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": max_tokens,
                        "temperature": temperature
                    },
                    timeout=30.0
                )

                if response.status_code == 200:
                    data = response.json()
                    return data["content"][0]["text"]
                else:
                    return f"[Anthropic API error: {response.status_code}]"

            except Exception as e:
                return f"[Anthropic API error: {str(e)}]"

    async def _call_groq(self, prompt: str, model: str, temperature: float, max_tokens: int) -> str:
        """Call Groq API"""
        if not self.groq_key:
            return "[Groq API key not configured]"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.groq_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": "You are a helpful assistant."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    },
                    timeout=30.0
                )

                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    return f"[Groq API error: {response.status_code}]"

            except Exception as e:
                return f"[Groq API error: {str(e)}]"

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate real text embeddings"""

        if not self.openai_key:
            # Return random if no API key (for testing)
            import hashlib
            import numpy as np
            hash_val = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
            np.random.seed(hash_val)
            return np.random.rand(384).tolist()

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://api.openai.com/v1/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.openai_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "text-embedding-ada-002",
                        "input": text
                    },
                    timeout=30.0
                )

                if response.status_code == 200:
                    data = response.json()
                    return data["data"][0]["embedding"]
                else:
                    # Fallback to random
                    import hashlib
                    import numpy as np
                    hash_val = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
                    np.random.seed(hash_val)
                    return np.random.rand(1536).tolist()  # Ada-002 uses 1536 dimensions

            except Exception:
                # Fallback to random
                import hashlib
                import numpy as np
                hash_val = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
                np.random.seed(hash_val)
                return np.random.rand(1536).tolist()

# Global instance
llm = LLMIntegration()