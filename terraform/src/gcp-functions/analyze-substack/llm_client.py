import asyncio
import os
from typing import Any, Optional, Type

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel, OpenAIModelSettings
from pydantic_ai.providers.openrouter import OpenRouterProvider


class LLMClient:
    """Abstraction layer for all LLM calls used by Cloud Functions.

    The client is built on top of ``pydantic-ai`` so that prompts can
    return either *raw strings* or *structured Pydantic models* depending
    on the ``output_type`` that is passed when invoking the LLM.

    Example
    -------
    >>> llm = LLMClient()
    >>> response = llm.run_prompt("Say hello world")
    >>> print(response)
    hello world

    With structured output:

    >>> class Foo(BaseModel):
    ...     bar: str
    ...
    >>> result: Foo = llm.run_prompt("{"bar": "baz"}", output_type=Foo)
    """

    def __init__(self):
        self.openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY")

        # Model configuration (shared across all Cloud Functions)
        self.model_primary: str = os.getenv(
            "OPENROUTER_MODEL_PRIMARY", "google/gemini-2.5-flash"
        )
        models_fallback_str: str = os.getenv(
            "OPENROUTER_MODELS_FALLBACK", "google/gemini-2.5-flash"
        )
        self.models_fallback: list[str] = [m.strip() for m in models_fallback_str.split(",")]
        self.temperature: float = float(os.getenv("OPENROUTER_MODEL_TEMPERATURE", "0.0"))

    async def _async_run(self, prompt: str, output_type: Optional[Type[BaseModel]] = None) -> Any:
        """Internal helper that performs the async LLM invocation."""
        model = OpenAIModel(
            self.model_primary,
            provider=OpenRouterProvider(api_key=self.openrouter_api_key),
        )
        agent = Agent(
            model,
            output_type=output_type,
            model_settings=OpenAIModelSettings(
                temperature=self.temperature, extra_body={"models": self.models_fallback}
            ),
            system_prompt="",
        )
        result = await agent.run(prompt)
        return result.output

    def run_prompt(self, prompt: str, output_type: Optional[Type[BaseModel]] = None) -> Any:
        """Run a prompt synchronously.

        Parameters
        ----------
        prompt: str
            The prompt to send to the LLM.
        output_type: Optional[Type[BaseModel]]
            When provided, the Agent will attempt to coerce the response
            into the given *pydantic* model. When *None*, a raw `str` is
            returned.
        """
        return asyncio.run(self._async_run(prompt, output_type))
