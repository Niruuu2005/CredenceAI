"""
LLM Client for CredenceAI Iteration 0.4

Provides a unified interface for calling various LLM providers (OpenAI, Anthropic, local models).
Handles retry logic, token counting, error handling, and budget tracking integration.

Supports:
- OpenAI API (GPT-3.5, GPT-4)
- Anthropic API (Claude)
- Local models via Ollama
- Configurable fallback providers
"""

import os
import asyncio
import time
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import tiktoken

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """
    Structured response from LLM API.
    
    Attributes:
        content: Generated text content
        model: Model used for generation
        tokens_used: Total tokens consumed (prompt + completion)
        prompt_tokens: Tokens in the prompt
        completion_tokens: Tokens in the completion
        finish_reason: Reason completion ended (stop, length, etc.)
        raw_response: Full API response for debugging
    """
    content: str
    model: str
    tokens_used: int
    prompt_tokens: int
    completion_tokens: int
    finish_reason: str
    raw_response: Optional[Dict[str, Any]] = None


class LLMError(Exception):
    """Base exception for LLM-related errors."""
    pass


class LLMTimeoutError(LLMError):
    """Raised when LLM request times out."""
    pass


class LLMRateLimitError(LLMError):
    """Raised when rate limit is exceeded."""
    pass


class LLMClient:
    """
    Unified client for interacting with LLM APIs.
    
    Features:
    - Automatic retry with exponential backoff
    - Token counting and budget tracking
    - Multiple provider support
    - Graceful error handling
    """
    
    # Default configuration
    DEFAULT_MODEL = "gpt-3.5-turbo"
    DEFAULT_MAX_TOKENS = 500
    DEFAULT_TEMPERATURE = 0.7
    DEFAULT_TIMEOUT = 30  # seconds
    MAX_RETRIES = 3
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize LLM client.
        
        Args:
            config: Optional configuration overrides
        """
        self.config = config or {}
        self.model = self.config.get("model", self.DEFAULT_MODEL)
        self.api_key = self.config.get("api_key") or os.getenv("OPENAI_API_KEY")
        self.timeout = self.config.get("timeout", self.DEFAULT_TIMEOUT)
        self.max_retries = self.config.get("max_retries", self.MAX_RETRIES)
        
        # Token encoder for counting (using tiktoken for OpenAI models)
        try:
            self.token_encoder = tiktoken.encoding_for_model(self.model)
        except Exception:
            # Fallback to cl100k_base for unknown models
            self.token_encoder = tiktoken.get_encoding("cl100k_base")
        
        logger.info(f"Initialized LLM client with model: {self.model}")
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using the model's tokenizer.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        try:
            return len(self.token_encoder.encode(text))
        except Exception as e:
            logger.warning(f"Token counting failed, using estimate: {e}")
            # Rough estimate: ~4 chars per token
            return len(text) // 4
    
    async def call_llm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Call the LLM API with retry logic.
        
        Args:
            prompt: User prompt/question
            system_prompt: Optional system instruction
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            **kwargs: Additional model-specific parameters
            
        Returns:
            LLMResponse with generated content and metadata
            
        Raises:
            LLMError: If all retries fail
            LLMTimeoutError: If request times out
            LLMRateLimitError: If rate limit exceeded
        """
        max_tokens = max_tokens or self.DEFAULT_MAX_TOKENS
        temperature = temperature if temperature is not None else self.DEFAULT_TEMPERATURE
        
        # Count prompt tokens
        prompt_text = f"{system_prompt}\n{prompt}" if system_prompt else prompt
        prompt_tokens = self.count_tokens(prompt_text)
        
        logger.debug(
            f"Calling LLM: model={self.model}, "
            f"prompt_tokens={prompt_tokens}, max_tokens={max_tokens}"
        )
        
        # Retry loop with exponential backoff
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = await self._make_api_call(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs
                )
                
                logger.info(
                    f"LLM call successful: tokens={response.tokens_used}, "
                    f"model={response.model}"
                )
                
                return response
                
            except LLMRateLimitError as e:
                last_error = e
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                logger.warning(
                    f"Rate limit hit (attempt {attempt + 1}/{self.max_retries}), "
                    f"retrying in {wait_time}s"
                )
                await asyncio.sleep(wait_time)
                
            except LLMTimeoutError as e:
                last_error = e
                logger.warning(
                    f"Timeout (attempt {attempt + 1}/{self.max_retries}), retrying"
                )
                
            except Exception as e:
                last_error = e
                logger.error(f"LLM call failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1)
        
        # All retries failed
        raise LLMError(f"LLM call failed after {self.max_retries} retries: {last_error}")
    
    async def _make_api_call(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
        **kwargs
    ) -> LLMResponse:
        """
        Make the actual API call (to be implemented with real API).
        
        For now, this is a mock implementation. In production, this would call:
        - OpenAI API for GPT models
        - Anthropic API for Claude models
        - Ollama for local models
        
        Args:
            prompt: User prompt
            system_prompt: System instruction
            max_tokens: Max tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters
            
        Returns:
            LLMResponse with generated content
        """
        # MOCK IMPLEMENTATION - Replace with real API calls in production
        if self.api_key:
            try:
                import httpx
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                }
                for k, v in kwargs.items():
                    payload[k] = v
                    
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    res = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers=headers,
                        json=payload
                    )
                    if res.status_code == 429:
                        raise LLMRateLimitError("OpenAI API rate limit exceeded")
                    elif res.status_code in (408, 504):
                        raise LLMTimeoutError("OpenAI API request timed out")
                    elif res.status_code != 200:
                        raise LLMError(f"OpenAI API call failed with status {res.status_code}: {res.text}")
                    
                    res_data = res.json()
                    choices = res_data.get("choices", [])
                    if not choices:
                        raise LLMError("OpenAI API returned no choices in response")
                    
                    message = choices[0].get("message", {})
                    content = message.get("content", "")
                    finish_reason = choices[0].get("finish_reason", "stop")
                    usage = res_data.get("usage", {})
                    
                    prompt_tokens_used = usage.get("prompt_tokens", 0)
                    completion_tokens_used = usage.get("completion_tokens", 0)
                    total_tokens_used = usage.get("total_tokens", prompt_tokens_used + completion_tokens_used)
                    
                    return LLMResponse(
                        content=content.strip(),
                        model=self.model,
                        tokens_used=total_tokens_used,
                        prompt_tokens=prompt_tokens_used,
                        completion_tokens=completion_tokens_used,
                        finish_reason=finish_reason,
                        raw_response=res_data
                    )
            except Exception as e:
                if isinstance(e, (LLMRateLimitError, LLMTimeoutError, LLMError)):
                    raise e
                logger.error(f"Real LLM call failed: {e}")
                if settings.APP_ENV == "production" and not settings.MOCK_SERVICES:
                    raise LLMError(f"OpenAI API call failed in production: {e}") from e
                logger.warning("Falling back to mock LLM response (non-production or MOCK_SERVICES)")

        # Simulate API latency
        await self._async_sleep(0.5)
        
        # Import json for proper JSON formatting
        import json
        
        # Mock response based on system prompt and prompt content
        # Check if this is a planner agent request (system prompt contains "planning agent")
        if system_prompt and "planning agent" in system_prompt.lower():
            # Extract user goal from prompt
            goal_match = prompt.split("User Goal:")[1].split("\n")[0].strip() if "User Goal:" in prompt else prompt[:100]
            
            # Generate appropriate mock JSON based on goal keywords
            if any(word in goal_match.lower() for word in ["company", "competitor", "perplexity", "tesla", "rivian"]):
                # Company research vertical
                entities = []
                if "perplexity" in goal_match.lower():
                    entities.append("Perplexity AI")
                if "tesla" in goal_match.lower():
                    entities.append("Tesla")
                if "rivian" in goal_match.lower():
                    entities.append("Rivian")
                
                entity_primary = entities[0] if entities else "company"
                entities_json = json.dumps(entities if entities else ["company"])
                
                mock_content = f"""{{
  "jobs": [
    {{
      "job_type": "search",
      "description": "Research {entity_primary} profile",
      "parameters": {{"entity": "{entity_primary}", "vertical": "company", "sources": ["Wikidata", "Wikipedia", "SearXNG"]}},
      "priority": 1,
      "dependencies": []
    }},
    {{
      "job_type": "search",
      "description": "Identify competitors",
      "parameters": {{"query": "{entity_primary} competitors", "vertical": "company"}},
      "priority": 2,
      "dependencies": []
    }}
  ],
  "entities": {entities_json},
  "recommended_verticals": ["company"],
  "success_metrics": ["Found company profile", "Identified competitors"],
  "reasoning": "Company intelligence request focusing on competitive landscape."
}}"""
            
            elif any(word in goal_match.lower() for word in ["news", "track", "breaking", "climate", "policy"]):
                # News monitoring vertical
                topic = "climate policy" if "climate" in goal_match.lower() else "news"
                mock_content = f"""{{
  "jobs": [
    {{
      "job_type": "monitor",
      "description": "Monitor {topic} news",
      "parameters": {{"topic": "{topic}", "vertical": "news", "sources": ["GDELT", "SearXNG_news"]}},
      "priority": 1,
      "dependencies": []
    }}
  ],
  "entities": ["{topic}"],
  "recommended_verticals": ["news"],
  "success_metrics": ["Daily updates", "Multiple news sources"],
  "reasoning": "News monitoring request with temporal tracking."
}}"""
            
            elif any(word in goal_match.lower() for word in ["paper", "research", "academic", "retrieval", "quantum"]):
                # Research vertical
                topic = "retrieval-augmented generation" if "retrieval" in goal_match.lower() else "quantum computing" if "quantum" in goal_match.lower() else "research"
                mock_content = f"""{{
  "jobs": [
    {{
      "job_type": "search",
      "description": "Search for papers on {topic}",
      "parameters": {{"query": "{topic}", "vertical": "research", "sources": ["OpenAlex", "arXiv"]}},
      "priority": 1,
      "dependencies": []
    }}
  ],
  "entities": ["{topic}"],
  "recommended_verticals": ["research"],
  "success_metrics": ["Found recent papers", "Identified citations"],
  "reasoning": "Academic research request for scholarly sources."
}}"""
            
            elif any(word in goal_match.lower() for word in ["dataset", "rag", "build"]) and not any(word in goal_match.lower() for word in ["paper", "research", "academic"]):
                # RAG dataset builder vertical
                topic = "AI safety" if "safety" in goal_match.lower() else "dataset"
                mock_content = f"""{{
  "jobs": [
    {{
      "job_type": "extract",
      "description": "Build RAG dataset on {topic}",
      "parameters": {{"topic": "{topic}", "vertical": "rag", "quality_filter": true}},
      "priority": 1,
      "dependencies": []
    }}
  ],
  "entities": ["{topic}"],
  "recommended_verticals": ["rag"],
  "success_metrics": ["Curated document collection", "Quality filtering applied"],
  "reasoning": "Dataset building request with quality filtering."
}}"""
            
            else:
                # Generic plan
                mock_content = """{{
  "jobs": [
    {{
      "job_type": "search",
      "description": "Execute search for user goal",
      "parameters": {{"vertical": "general", "sources": ["SearXNG"]}},
      "priority": 1,
      "dependencies": []
    }}
  ],
  "entities": ["general"],
  "recommended_verticals": ["general"],
  "success_metrics": ["Found relevant results"],
  "reasoning": "General search request."
}}"""
        
        elif "quality" in prompt.lower() or "assess" in prompt.lower():
            mock_content = """
            Quality Assessment:
            - Relevance: HIGH (directly addresses the query)
            - Freshness: MEDIUM (published 3 months ago)
            - Source Reliability: HIGH (established source with good track record)
            - Recommendation: ACCEPT for indexing
            """
        elif "entity" in prompt.lower() or "disambiguate" in prompt.lower():
            mock_content = """
            Entity Disambiguation:
            Canonical Entity: "Apple Inc."
            Confidence: 0.92
            Reasoning: Context mentions "iPhone", "Cupertino", and "tech company"
            Alternative: "apple (fruit)" rejected due to lack of agricultural context
            """
        else:
            mock_content = f"Mock LLM response for: {prompt[:100]}..."
        
        # Calculate mock token usage
        prompt_text = f"{system_prompt}\n{prompt}" if system_prompt else prompt
        prompt_tokens = self.count_tokens(prompt_text)
        completion_tokens = self.count_tokens(mock_content)
        
        return LLMResponse(
            content=mock_content.strip(),
            model=self.model,
            tokens_used=prompt_tokens + completion_tokens,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            finish_reason="stop",
            raw_response={"mock": True}
        )
    
    async def _async_sleep(self, seconds: float):
        """Async sleep helper."""
        import asyncio
        await asyncio.sleep(seconds)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        return {
            "model": self.model,
            "max_tokens": self.DEFAULT_MAX_TOKENS,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
        }


# Convenience functions for common LLM operations

async def generate_text(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    **kwargs
) -> str:
    """
    Simple text generation function.
    
    Args:
        prompt: User prompt
        system_prompt: Optional system instruction
        model: Model to use (default: gpt-3.5-turbo)
        **kwargs: Additional parameters
        
    Returns:
        Generated text content
    """
    config = {"model": model} if model else {}
    client = LLMClient(config=config)
    response = await client.call_llm(prompt, system_prompt, **kwargs)
    return response.content


async def extract_json(
    prompt: str,
    system_prompt: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Generate and parse JSON response.
    
    Args:
        prompt: User prompt requesting JSON
        system_prompt: Optional system instruction
        **kwargs: Additional parameters
        
    Returns:
        Parsed JSON as dictionary
    """
    import json
    
    json_system_prompt = (
        "You are a helpful assistant that always responds with valid JSON. "
        "Do not include any text before or after the JSON object."
    )
    
    if system_prompt:
        json_system_prompt = f"{system_prompt}\n{json_system_prompt}"
    
    client = LLMClient()
    response = await client.call_llm(prompt, json_system_prompt, **kwargs)
    
    try:
        # Try to parse JSON from response
        content = response.content.strip()
        # Remove markdown code blocks if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        return json.loads(content.strip())
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from LLM response: {e}")
        raise LLMError(f"Invalid JSON response: {e}")
