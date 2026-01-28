import os
import logging
import httpx
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from project root
# Find the .env file by going up from this file's location
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)


class OpenRouterClient:
    """
    Client for calling OpenRouter.ai API.
    Responsible ONLY for making HTTP requests to OpenRouter.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        http_referer: Optional[str] = None,
        app_title: Optional[str] = None
    ):
        """
        Initialize OpenRouter client with configuration from env vars or parameters.
        
        Args:
            api_key: OpenRouter API key (defaults to env OPENROUTER_API_KEY)
            base_url: Base URL (defaults to env OPENROUTER_BASE_URL or https://openrouter.ai/api/v1)
            model: Default model to use (defaults to env OPENROUTER_MODEL)
            http_referer: HTTP referer header (defaults to env OPENROUTER_HTTP_REFERER)
            app_title: App title header (defaults to env OPENROUTER_APP_TITLE)
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.base_url = base_url or os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        self.default_model = model or os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
        self.http_referer = http_referer or os.getenv("OPENROUTER_HTTP_REFERER", "")
        self.app_title = app_title or os.getenv("OPENROUTER_APP_TITLE", "Thai PDF OCR API")
        
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key is required. "
                "Set OPENROUTER_API_KEY environment variable or pass api_key parameter."
            )
    
    def call_openrouter(
        self,
        messages: list,
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        timeout: int = 60
    ) -> str:
        """
        Call OpenRouter API with chat completion request.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (defaults to instance default_model)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
            timeout: Request timeout in seconds
            
        Returns:
            Raw string response from the model
            
        Raises:
            httpx.HTTPError: If request fails
            ValueError: If response format is unexpected
        """
        model = model or self.default_model
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Add optional headers if configured
        if self.http_referer:
            headers["HTTP-Referer"] = self.http_referer
        if self.app_title:
            headers["X-Title"] = self.app_title
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        url = f"{self.base_url}/chat/completions"
        
        logger.info(f"Calling OpenRouter API with model: {model}")
        logger.debug(f"Request payload: {payload}")
        
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                
                result = response.json()
                
                # Extract content from OpenAI-compatible response format
                if "choices" not in result or len(result["choices"]) == 0:
                    raise ValueError("No choices in OpenRouter response")
                
                content = result["choices"][0].get("message", {}).get("content", "")
                
                if not content:
                    raise ValueError("Empty content in OpenRouter response")
                
                logger.info(f"OpenRouter API call successful, received {len(content)} characters")
                return content
                
        except httpx.HTTPStatusError as e:
            logger.error(f"OpenRouter API HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.TimeoutException:
            logger.error(f"OpenRouter API timeout after {timeout}s")
            raise
        except Exception as e:
            logger.error(f"OpenRouter API error: {str(e)}")
            raise
