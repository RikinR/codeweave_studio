"""Groq chat completion client for optional function description enrichment.

Wraps the Groq SDK with logging and error translation. Used by
:mod:`application.ingestion.summarize_description` when heuristics are insufficient.
"""

from __future__ import annotations
from groq import Groq
from infrastructure.llm.config import GROQ_API_KEY, GROQ_MODEL
from infrastructure.logging.logger import get_logger
logger = get_logger(__name__)

class GroqError(RuntimeError):
    """Raised when Groq is misconfigured or the API request fails."""

def _client() -> Groq:
    if not GROQ_API_KEY:
        raise GroqError('GROQ_API_KEY is not set. Add it to backend/.env before running queries.')
    return Groq(api_key=GROQ_API_KEY)

def chat_completion(messages: list[dict], model: str | None=None, *, temperature: float=0.2, max_tokens: int=1024) -> str:
    """Run a non-streaming chat completion and return the assistant message text."""
    if not messages:
        raise GroqError('messages must not be empty')
    model_name = model or GROQ_MODEL
    logger.debug('groq: chat model=%s messages=%d', model_name, len(messages))
    try:
        response = _client().chat.completions.create(model=model_name, messages=messages, temperature=temperature, max_tokens=max_tokens)
    except Exception as exc:
        logger.error('groq: chat completion failed', exc_info=True)
        raise GroqError(f'Groq chat completion failed: {exc}') from exc
    content = response.choices[0].message.content
    if not content:
        raise GroqError('Groq returned an empty response')
    logger.info('groq: received response (%d chars)', len(content))
    return content
