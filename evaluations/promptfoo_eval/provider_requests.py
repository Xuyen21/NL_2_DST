import os
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from prompt_strategy.prompts import SYSTEM_PROMPT, ONE_PHASE_PROMPT, PROMPT_1, PROMPT_2
from text_to_json.schema_design import DomainStory
from utils.api_request import api_response

from typing import Any
from dotenv import load_dotenv

load_dotenv()

import litellm

litellm.drop_params = True


class ApiCall:
    def __init__(self, prompt: str, options: dict[str, Any], context: dict[str, Any]):
        config = options.get("config", {})
        self.model_name = config["model"]
        self.provider_name = config.get("provider")
        base_env_name = config.get("base")
        self.api_base = os.environ.get(base_env_name) if base_env_name else None
        api_key_env_name = config.get("api_key_env")
        resolved_api_key_env_name = api_key_env_name or self.resolve_api_key_env_name(self.provider_name)
        self.api_key = os.environ.get(resolved_api_key_env_name) if resolved_api_key_env_name else None
        self.user_story = context["vars"]["input"]
        self.timeout_seconds = float(os.getenv("LLM_TIMEOUT_SECONDS", "120"))
        self.phase_gap_seconds = max(0.0, float(os.getenv("LLM_PHASE_GAP_SECONDS", "0")))

    @staticmethod
    def resolve_custom_llm_provider(provider_name: str | None) -> str | None:
        if provider_name == "qwen-compatible":
            return "openai"
        return provider_name

    @staticmethod
    def resolve_api_key_env_name(provider_name: str | None) -> str | None:
        provider_to_key_env = {
            "qwen-compatible": "DASHSCOPE_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
            "openai": "OPENAI_API_KEY",
            "mistral": "MISTRAL_API_KEY",
            "xai": "XAI_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
        }
        if provider_name is None:
            return None
        return provider_to_key_env.get(provider_name)

    @staticmethod
    def create_messages(user_prompt: str) -> list:
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

    def _call_api(self, messages: list, schema=None) -> dict:
        return api_response(
            model_name=self.model_name,
            messages=messages,
            schema=schema,
            api_key=self.api_key,
            api_base=self.api_base,
            custom_llm_provider=self.resolve_custom_llm_provider(self.provider_name),
            timeout_seconds=self.timeout_seconds,
        )

    @staticmethod
    def _finalize_output(domain_story: DomainStory) -> dict:
        return domain_story.model_dump(mode="json")

    @staticmethod
    def _raise_with_details(e: Exception) -> None:
        detailed_message = getattr(e, "_api_request_details", None) or f"{e.__class__.__name__}: {e}"
        attempts = getattr(e, "_api_request_attempts", None)
        attempt_suffix = f" after {attempts} attempt(s)" if attempts else ""
        setattr(e, "promptfoo_error_detail", detailed_message)

        if isinstance(e, litellm.RateLimitError):
            raise RuntimeError(f"429 Rate Limit{attempt_suffix}: {detailed_message}") from e
        if isinstance(e, litellm.ServiceUnavailableError):
            raise RuntimeError(f"503 Service Unavailable{attempt_suffix}: {detailed_message}") from e

        error_msg = str(e)
        lowered_error_msg = error_msg.lower()
        if "429" in error_msg or "rate limit" in lowered_error_msg or "too many requests" in lowered_error_msg:
            raise RuntimeError(f"429 Rate Limit{attempt_suffix}: {detailed_message}") from e
        if "503" in error_msg or "service unavailable" in lowered_error_msg:
            raise RuntimeError(f"503 Service Unavailable{attempt_suffix}: {detailed_message}") from e

        raise RuntimeError(f"Provider failed{attempt_suffix}: {detailed_message}") from e

    @staticmethod
    def _combine_token_usage(usage_1: dict | None, usage_2: dict | None) -> dict | None:
        if usage_1 and usage_2:
            return {
                "prompt": usage_1["prompt"] + usage_2["prompt"],
                "completion": usage_1["completion"] + usage_2["completion"],
                "total": usage_1["total"] + usage_2["total"],
            }
        return usage_2

    def one_phase_call(self):
        user_prompt = ONE_PHASE_PROMPT.format(user_story=self.user_story)
        messages = self.create_messages(user_prompt)

        try:
            resp = self._call_api(messages, schema=DomainStory)
            return {
                "output": self._finalize_output(resp["output"]),
                "token_usage": resp["token_usage"],
            }
        except Exception as e:
            self._raise_with_details(e)

    def two_phase_zeroshot_call(self):
        prompt_1 = PROMPT_1.format(user_story=self.user_story)
        messages = self.create_messages(prompt_1)

        try:
            response_1 = self._call_api(messages, schema=None)

            messages.append({"role": "assistant", "content": response_1["output"]})
            messages.append({"role": "user", "content": PROMPT_2})

            if self.phase_gap_seconds > 0:
                time.sleep(self.phase_gap_seconds)

            response_2 = self._call_api(messages, schema=DomainStory)

            return {
                "output": self._finalize_output(response_2["output"]),
                "token_usage": self._combine_token_usage(
                    response_1["token_usage"], response_2["token_usage"]
                ),
            }
        except Exception as e:
            self._raise_with_details(e)


def one_phase_zeroshot(prompt: str, options: dict[str, Any], context: dict[str, Any]):
    api_call = ApiCall(prompt, options, context)
    return api_call.one_phase_call()


def two_phase_zeroshot(prompt: str, options: dict[str, Any], context: dict[str, Any]):
    api_call = ApiCall(prompt, options, context)
    return api_call.two_phase_zeroshot_call()


PROMPTFOO_PROVIDER_ALIASES = (
    "gpt",
    "gemini",
    "claude",
    "grok",
    "qwen",
    "deepseek",
)


for alias in PROMPTFOO_PROVIDER_ALIASES:
    globals()[f"one_phase_zeroshot_{alias}"] = one_phase_zeroshot
    globals()[f"two_phase_zeroshot_{alias}"] = two_phase_zeroshot
