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

# Drops unsupported params globally without throwing an error
litellm.drop_params = True


class ApiCall:
    def __init__(self, prompt: str, options: dict[str, Any], context: dict[str, Any]):
        # prompt param is the top level prompt in yaml which is null, but promptfoo requires this param in this api call
        self.model_name = options["config"]["model"]  # options.get("config", {}).get("model")
        self.user_story = context["vars"]["input"]

    @staticmethod
    def create_messages(user_prompt: str) -> list:
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

    @staticmethod
    def get_token_usage(resp) -> dict[str, Any] | None:
        usage = None
        if getattr(resp, "usage", None) is not None:
            usage = {
                "prompt": resp.usage.prompt_tokens,
                "completion": resp.usage.completion_tokens,
                "total": resp.usage.total_tokens,
            }
        return usage

    def one_phase_call(self):
        user_prompt = ONE_PHASE_PROMPT.format(user_story=self.user_story)
        messages = self.create_messages(user_prompt)

        # resp = litellm.completion(
        #     model="gpt-5.4",
        #     messages=messages,
        #     response_format=DomainStory
        # )
        try:
            resp = api_response(model_name=self.model_name, messages=messages, schema=DomainStory)

            # output = resp.choices[0].message.content
            update_icons = search_icons(resp['output'])
            final_json_output = update_icons.model_dump(mode="json")

            # token_used = self.get_token_usage(resp)

            return {"output": final_json_output,
                    "token_usage": resp['token_usage'],
                    }
        except litellm.ServiceUnavailableError as e:
            # RETURN the error to Promptfoo instead of crashing!
            # The keywords "503" or "service unavailable" will trigger Promptfoo's internal retry.
            return {"error": f"503 Service Unavailable: {str(e)}"}

        except litellm.RateLimitError as e:
            # Triggers AIMD backoff for rate limits
            return {"error": f"429 Rate Limit: {str(e)}"}

        # 3. Catch-all for any other LiteLLM or HTTP crashes
        except Exception as e:
            error_msg = str(e)
            # If the string contains 503, format it so Promptfoo knows to retry
            if "503" in error_msg:
                return {"error": f"503 Service Unavailable: {error_msg}"}
            return {"error": f"Provider failed: {error_msg}"}

    def two_phase_zeroshot_call(self):
        prompt_1 = PROMPT_1.format(user_story=self.user_story)
        messages = self.create_messages(prompt_1)

        response = litellm.completion(
            model="gpt-5.4",
            messages=messages,
            temperature=0.0,
            seed=42
        )
        result_1 = response.choices[0].message.content
        print("result_1: \n", result_1)

        # output_1 = api_response(model_name="gpt-5.4", messages=messages)
        messages.append({"role": "assistant", "content": result_1})
        messages.append({"role": "user", "content": PROMPT_2})

        response_2 = litellm.completion(
            model="gpt-5.4",
            messages=messages,
            response_format=DomainStory,
            temperature=0.0
        )


def one_phase_zeroshot(prompt: str, options: dict[str, Any], context: dict[str, Any]):
    api_call = ApiCall(prompt, options, context)
    return api_call.one_phase_call()


# def two_phase_zeroshot(prompt: str, options: dict[str, Any], context: dict[str, Any]):
#     config = options.get("config", {})
#     model_name = config.get("model")


# One phase prompting
one_phase_zeroshot_gpt = one_phase_zeroshot
one_phase_zeroshot_claude = one_phase_zeroshot_gpt
one_phase_zeroshot_gemini = one_phase_zeroshot
