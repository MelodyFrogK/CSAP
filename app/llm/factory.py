"""설정에 따라 LLM 공급자를 생성한다."""
from __future__ import annotations

from functools import lru_cache

from ..config import get_settings
from .base import LLMError, LLMProvider


@lru_cache
def get_provider() -> LLMProvider:
    s = get_settings()
    provider = (s.llm_provider or "echo").lower()
    if provider == "anthropic":
        from .anthropic_provider import AnthropicProvider

        return AnthropicProvider(model=s.anthropic_model)
    if provider == "openai":
        from .openai_provider import OpenAIProvider

        return OpenAIProvider(model=s.openai_model)
    if provider in ("claude_cli", "claude-cli", "cli"):
        from .claude_cli_provider import ClaudeCliProvider

        return ClaudeCliProvider(
            binary=s.claude_cli_binary,
            model=s.claude_cli_model,
            timeout=s.claude_cli_timeout,
        )
    if provider == "echo":
        from .echo_provider import EchoProvider

        return EchoProvider()
    raise LLMError(f"알 수 없는 LLM 공급자: {provider}")
