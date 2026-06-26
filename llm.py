"""
LLM Client Module
Handles communication with OpenRouter API for LLM inference
"""

import os
import time
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv()


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
DEFAULT_MODEL = os.getenv("MODEL", os.getenv("OPENROUTER_DEFAULT_MODEL", "gpt-3.5-turbo"))
BASE_URL = "https://openrouter.ai/api/v1"
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "60"))


# ── Exceptions ──


class LLMError(Exception):
    """Base exception for LLM-related errors."""
    pass


class AuthenticationError(LLMError):
    """Raised when the API key is invalid or missing."""
    pass


class RateLimitError(LLMError):
    """Raised when the API rate limit has been exceeded."""
    pass


class TimeoutError(LLMError):
    """Raised when the API request times out."""
    pass


class NetworkError(LLMError):
    """Raised when a network-related failure occurs."""
    pass


# ── Core Function ──


def call_llm(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 1024,
    timeout: int = REQUEST_TIMEOUT,
) -> str:
    """
    Send a prompt to the OpenRouter API and return the generated response.

    Reads OPENROUTER_API_KEY and MODEL from the .env file by default.

    Parameters
    ----------
    prompt : str
        The user prompt to send to the LLM.
    system_prompt : str, optional
        A system-level instruction to set the assistant's behavior.
    model : str, optional
        The model identifier to use. Falls back to MODEL env var, then
        OPENROUTER_DEFAULT_MODEL, then 'gpt-3.5-turbo'.
    api_key : str, optional
        OpenRouter API key. Falls back to OPENROUTER_API_KEY env var.
    temperature : float
        Sampling temperature (0.0 to 2.0). Default 0.7.
    max_tokens : int
        Maximum tokens in the generated response. Default 1024.
    timeout : int
        Request timeout in seconds. Default 60.

    Returns
    -------
    str
        The generated response text only.

    Raises
    ------
    AuthenticationError
        If the API key is missing or invalid.
    RateLimitError
        If the API rate limit is exceeded.
    TimeoutError
        If the request times out.
    NetworkError
        If a network failure occurs.
    """
    key = api_key or OPENROUTER_API_KEY
    if not key:
        raise AuthenticationError(
            "OpenRouter API key is not set. "
            "Add OPENROUTER_API_KEY to your .env file or pass api_key directly."
        )

    selected_model = model or DEFAULT_MODEL

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": selected_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            f"{BASE_URL}/chat/completions",
            json=payload,
            headers=headers,
            timeout=timeout,
        )
    except requests.exceptions.Timeout:
        raise TimeoutError(
            f"Request to OpenRouter timed out after {timeout}s. "
            "Try increasing the timeout or check your network connectivity."
        )
    except requests.exceptions.ConnectionError:
        raise NetworkError(
            "Failed to connect to OpenRouter API. "
            "Check your internet connection or the API endpoint URL."
        )
    except requests.exceptions.RequestException as e:
        raise NetworkError(f"A network error occurred: {e}")

    # ── Handle HTTP status codes ──
    if response.status_code == 401:
        raise AuthenticationError(
            "Invalid API key. Check your OPENROUTER_API_KEY in .env."
        )

    if response.status_code == 403:
        raise AuthenticationError(
            "Access forbidden. Your API key may not have permission for this model."
        )

    if response.status_code == 429:
        retry_after = response.headers.get("Retry-After", "unknown")
        raise RateLimitError(
            f"Rate limit exceeded. Retry after {retry_after} seconds."
        )

    if response.status_code == 402:
        raise RateLimitError(
            "Insufficient credits or quota exceeded. "
            "Check your OpenRouter billing dashboard."
        )

    if response.status_code >= 500:
        raise LLMError(
            f"OpenRouter server error (HTTP {response.status_code}). "
            "Please try again later."
        )

    if response.status_code != 200:
        try:
            error_detail = response.json()
            error_msg = error_detail.get("error", {}).get(
                "message", response.text
            )
        except Exception:
            error_msg = response.text
        raise LLMError(
            f"OpenRouter returned HTTP {response.status_code}: {error_msg}"
        )

    # ── Parse success response ──
    try:
        data = response.json()
        generated_text = data["choices"][0]["message"]["content"]
        return generated_text.strip()
    except (KeyError, IndexError, ValueError) as e:
        raise LLMError(f"Failed to parse LLM response: {e}")


# ── Client Class (for stateful use) ──


class LLMClient:
    """Client for interacting with OpenRouter API to run LLM inference."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = REQUEST_TIMEOUT,
    ):
        """Initialize the LLM client with an API key and default model."""
        self.api_key = api_key or OPENROUTER_API_KEY
        self.model = model or DEFAULT_MODEL
        self.timeout = timeout
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def list_models(self) -> List[Dict[str, Any]]:
        """Fetch and return the list of available models from OpenRouter."""
        try:
            response = requests.get(
                f"{BASE_URL}/models",
                headers=self.headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Failed to fetch models: {e}")

    def set_model(self, model: str) -> None:
        """Set the model to use for inference."""
        self.model = model

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs,
    ) -> str:
        """Send a prompt to the LLM and return the generated response."""
        return call_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            model=kwargs.get("model", self.model),
            api_key=self.api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=self.timeout,
        )

    def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs,
    ):
        """Send a prompt to the LLM and yield response chunks as they arrive."""
        key = self.api_key
        selected_model = kwargs.get("model", self.model)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": selected_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        try:
            with requests.post(
                f"{BASE_URL}/chat/completions",
                json=payload,
                headers=self.headers,
                timeout=self.timeout,
                stream=True,
            ) as response:
                if response.status_code == 401:
                    raise AuthenticationError("Invalid API key.")
                if response.status_code == 429:
                    raise RateLimitError("Rate limit exceeded.")
                response.raise_for_status()

                for line in response.iter_lines():
                    if line:
                        line = line.decode("utf-8").strip()
                        if line.startswith("data: ") and line != "data: [DONE]":
                            try:
                                import json
                                chunk = json.loads(line[6:])
                                delta = chunk["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                            except (json.JSONDecodeError, KeyError, IndexError):
                                continue
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Stream request timed out after {self.timeout}s.")
        except requests.exceptions.ConnectionError:
            raise NetworkError("Failed to connect to OpenRouter.")
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Stream error: {e}")

    def count_tokens(self, text: str) -> int:
        """Estimate the number of tokens in a given text string (approximate)."""
        # Simple estimation: ~4 characters per token for English text
        return max(1, len(text) // 4)


class LLMResponse:
    """Wrapper for LLM response data including metadata."""

    def __init__(
        self,
        text: str,
        model: str,
        usage: Optional[Dict[str, int]] = None,
        raw: Optional[Dict[str, Any]] = None,
    ):
        """Initialize an LLM response with text, model info, and usage stats."""
        self.text = text
        self.model = model
        self.usage = usage or {}
        self.raw = raw or {}

    def get_token_usage(self) -> Dict[str, int]:
        """Return token usage statistics (prompt, completion, total)."""
        return self.usage

    def get_cost_estimate(self) -> float:
        """Estimate the cost of this API call based on token usage."""
        # Approximate pricing per 1K tokens for common models
        pricing = {
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "claude-3-opus": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet": {"input": 0.003, "output": 0.015},
            "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
        }
        model_key = self.model
        if model_key not in pricing:
            return 0.0

        prompt_tokens = self.usage.get("prompt_tokens", 0)
        completion_tokens = self.usage.get("completion_tokens", 0)
        rates = pricing[model_key]

        cost = (prompt_tokens / 1000) * rates["input"] + \
               (completion_tokens / 1000) * rates["output"]
        return round(cost, 6)