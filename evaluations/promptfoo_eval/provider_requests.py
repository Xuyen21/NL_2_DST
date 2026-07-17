import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from icons_module.icon_semantic_search_2 import search_icons
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
        )

    @staticmethod
    def _finalize_output(domain_story) -> dict:
        updated = search_icons(domain_story)
        return updated.model_dump(mode="json")

    @staticmethod
    def _handle_error(e: Exception) -> dict:
        if isinstance(e, litellm.ServiceUnavailableError):
            return {"error": f"503 Service Unavailable: {str(e)}"}
        if isinstance(e, litellm.RateLimitError):
            return {"error": f"429 Rate Limit: {str(e)}"}
        error_msg = str(e)
        if "503" in error_msg:
            return {"error": f"503 Service Unavailable: {error_msg}"}
        return {"error": f"Provider failed: {error_msg}"}

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
            return self._handle_error(e)

    def two_phase_zeroshot_call(self):
        prompt_1 = PROMPT_1.format(user_story=self.user_story)
        messages = self.create_messages(prompt_1)

        try:
            response_1 = self._call_api(messages, schema=None)

            messages.append({"role": "assistant", "content": response_1["output"]})
            messages.append({"role": "user", "content": PROMPT_2})

            response_2 = self._call_api(messages, schema=DomainStory)

            return {
                "output": self._finalize_output(response_2["output"]),
                "token_usage": self._combine_token_usage(
                    response_1["token_usage"], response_2["token_usage"]
                ),
            }
        except Exception as e:
            return self._handle_error(e)


def one_phase_zeroshot(prompt: str, options: dict[str, Any], context: dict[str, Any]):
    api_call = ApiCall(prompt, options, context)
    return api_call.one_phase_call()


def two_phase_zeroshot(prompt: str, options: dict[str, Any], context: dict[str, Any]):
    api_call = ApiCall(prompt, options, context)
    return api_call.two_phase_zeroshot_call()


# One phase prompting
one_phase_zeroshot_gpt = one_phase_zeroshot
one_phase_zeroshot_qwen = one_phase_zeroshot
one_phase_zeroshot_glm = one_phase_zeroshot
one_phase_zeroshot_deepseek = one_phase_zeroshot

# Two phase prompting
two_phase_zeroshot_gpt = two_phase_zeroshot
two_phase_zeroshot_qwen = two_phase_zeroshot
two_phase_zeroshot_glm = two_phase_zeroshot
two_phase_zeroshot_deepseek = two_phase_zeroshot
