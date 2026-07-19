from pathlib import Path


def load_provider_models(promptfoo_config_path: Path) -> dict[str, str]:
    provider_models: dict[str, str] = {}
    current_provider_id: str | None = None
    in_providers = False
    in_config = False

    for raw_line in promptfoo_config_path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()

        if not stripped or stripped.startswith("#"):
            continue

        if stripped == "providers:":
            in_providers = True
            in_config = False
            current_provider_id = None
            continue

        if in_providers and stripped == "tests:":
            break

        if not in_providers:
            continue

        if stripped.startswith("- id:"):
            current_provider_id = stripped.split(":", 1)[1].strip()
            in_config = False
            continue

        if stripped == "config:":
            in_config = True
            continue

        if in_config and current_provider_id and stripped.startswith("model:"):
            provider_models[current_provider_id] = stripped.split(":", 1)[1].strip()

    return provider_models


def extract_prompt_variant(provider_id: str) -> str:
    prompt_variant = provider_id.rsplit(":", 1)[-1].strip()
    if prompt_variant.startswith("one_phase"):
        return "one_phase"
    if prompt_variant.startswith("two_phase"):
        return "two_phase"
    return prompt_variant or "unknown_phase"


def extract_prompting_mode(provider_id: str) -> str:
    prompt_variant = extract_prompt_variant(provider_id)
    if prompt_variant == "one_phase":
        return "one-phase"
    if prompt_variant == "two_phase":
        return "two-phase"
    return prompt_variant.replace("_", "-")

