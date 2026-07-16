import json
import re
from pathlib import Path

from mapping_code.json_to_plantuml import create_plantuml_syntax

PROJECT_ROOT = Path(__file__).resolve().parent
RESULTS_PATH = PROJECT_ROOT / "evaluations" / "results-zero-shot-qwenmax.json"
PROMPTFOO_CONFIG_PATH = PROJECT_ROOT / "evaluations" / "promptfoo-eval" / "promptfooconfig.yaml"
OUTPUT_DIR = PROJECT_ROOT / "manual_evaluation_output"


def slugify(value: str) -> str:
	compact = re.sub(r"\s+", "-", value.strip())
	safe = re.sub(r"[^A-Za-z0-9._-]", "", compact)
	return safe.strip("-") or "untitled"


def read_json(path: Path) -> dict:
	with path.open("r", encoding="utf-8") as file:
		return json.load(file)


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


def build_output_path(output_dir: Path, story_title: str, model_name: str) -> Path:
	base_name = f"results-{slugify(story_title)}-{slugify(model_name)}"
	output_path = output_dir / f"{base_name}.puml"
	suffix = 2

	while output_path.exists():
		output_path = output_dir / f"{base_name}-{suffix}.puml"
		suffix += 1

	return output_path


def export_promptfoo_results(
	results_path: Path = RESULTS_PATH,
	promptfoo_config_path: Path = PROMPTFOO_CONFIG_PATH,
	output_dir: Path = OUTPUT_DIR,
) -> list[Path]:
	report = read_json(results_path)
	provider_models = load_provider_models(promptfoo_config_path)
	output_dir.mkdir(parents=True, exist_ok=True)

	written_files: list[Path] = []
	for entry in report.get("results", {}).get("results", []):
		story_json = entry.get("response", {}).get("output")
		if not isinstance(story_json, dict) or "title" not in story_json:
			continue

		provider_id = str(entry.get("provider", {}).get("id", "unknown-provider"))
		model_name = str(provider_models.get(provider_id, provider_id.rsplit(":", 1)[-1]))

		plantuml_text = create_plantuml_syntax(story_json)
		output_path = build_output_path(output_dir, story_json["title"], model_name)
		output_path.write_text(plantuml_text, encoding="utf-8")
		written_files.append(output_path)

	return written_files


if __name__ == "__main__":
	generated_files = export_promptfoo_results()
	print(f"Generated {len(generated_files)} PlantUML files in {OUTPUT_DIR}")
	for path in generated_files:
		print(path.name)
