import json
import re
import textwrap
from dataclasses import dataclass
from pathlib import Path

import requests
from plantuml import deflate_and_encode

from mapping_code.json_to_plantuml import create_plantuml_syntax

PROJECT_ROOT = Path(__file__).resolve().parent
RESULTS_PATH = PROJECT_ROOT / "evaluations" / "results-zero-shot-CoT-v0-1-2.json"
PROMPTFOO_CONFIG_PATH = PROJECT_ROOT / "evaluations" / "promptfoo-eval" / "promptfooconfig.yaml"
OUTPUT_DIR = PROJECT_ROOT / "manual_evaluation_output"
PLANTUML_VALIDATION_URL = "https://www.plantuml.com/plantuml/txt/"
VALIDATION_TIMEOUT_SECONDS = 30
MAX_ACTIVITY_ARGUMENT_COMMAS = 5


@dataclass(slots=True)
class ExportStatus:
	story_title: str
	model_name: str
	success: bool
	output_path: Path | None = None
	reason: str | None = None


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
	return output_dir / f"{base_name}.puml"


def summarize_validation_error(response_text: str, status_code: int) -> str:
	lines = [line.strip() for line in response_text.splitlines() if line.strip()]
	from_line = next((line for line in lines if line.startswith("[From ")), None)
	syntax_line = next((line for line in lines if "Syntax Error?" in line), None)
	error_line = next((line for line in lines if "Error" in line and line != syntax_line), None)
	offending_line = None

	for index, line in enumerate(lines):
		if set(line) == {"^"} and index > 0:
			offending_line = lines[index - 1]
			break

	parts = [part for part in (from_line, syntax_line, error_line) if part]
	if offending_line:
		parts.append(f"Near: {textwrap.shorten(offending_line, width=140, placeholder='...')}")

	if parts:
		return " | ".join(str(part) for part in parts)

	return f"PlantUML validation failed with HTTP {status_code}"


def has_plantuml_syntax_error(response_text: str) -> bool:
	normalized = response_text.casefold()
	markers = (
		"syntax error?",
		"[from <",
		"error line",
		"cannot open include file",
	)
	return any(marker in normalized for marker in markers)


def obvious_domain_story_issue(plantuml_text: str) -> str | None:
	for line_number, line in enumerate(plantuml_text.splitlines(), start=1):
		stripped = line.strip()
		if not stripped.startswith("activity("):
			continue

		opening_parenthesis = stripped.find("(")
		closing_parenthesis = stripped.rfind(")")
		if opening_parenthesis == -1 or closing_parenthesis == -1 or closing_parenthesis <= opening_parenthesis:
			continue

		argument_text = stripped[opening_parenthesis + 1:closing_parenthesis]
		comma_count = argument_text.count(",")
		if comma_count > MAX_ACTIVITY_ARGUMENT_COMMAS:
			snippet = textwrap.shorten(stripped, width=140, placeholder="...")
			return (
				f"Detected invalid activity(...) call at line {line_number}: "
				f"found {comma_count + 1} comma-separated arguments. Near: {snippet}"
			)

	return None


def validate_plantuml_text(plantuml_text: str, session: requests.Session | None = None) -> tuple[bool, str | None]:
	obvious_issue = obvious_domain_story_issue(plantuml_text)
	if obvious_issue:
		return False, obvious_issue

	request_session = session or requests.Session()
	validation_url = PLANTUML_VALIDATION_URL + deflate_and_encode(plantuml_text)

	try:
		response = request_session.get(validation_url, timeout=VALIDATION_TIMEOUT_SECONDS)
	except requests.RequestException as exc:
		return False, f"PlantUML validation request failed: {exc}"

	if response.status_code == 200 and not has_plantuml_syntax_error(response.text):
		return True, None

	return False, summarize_validation_error(response.text, response.status_code)


def export_promptfoo_results(
	results_path: Path = RESULTS_PATH,
	promptfoo_config_path: Path = PROMPTFOO_CONFIG_PATH,
	output_dir: Path = OUTPUT_DIR,
) -> list[ExportStatus]:
	report = read_json(results_path)
	provider_models = load_provider_models(promptfoo_config_path)
	output_dir.mkdir(parents=True, exist_ok=True)

	request_session = requests.Session()
	export_statuses: list[ExportStatus] = []
	for entry in report.get("results", {}).get("results", []):
		provider_id = str(entry.get("provider", {}).get("id", "unknown-provider"))
		model_name = str(provider_models.get(provider_id, provider_id.rsplit(":", 1)[-1]))

		story_json = entry.get("response", {}).get("output")
		if not isinstance(story_json, dict):
			continue

		story_title = str(story_json.get("title", "untitled"))
		output_path = build_output_path(output_dir, story_title, model_name)
		if "title" not in story_json:
			if output_path.exists():
				output_path.unlink()
			export_statuses.append(ExportStatus(
				story_title=story_title,
				model_name=model_name,
				success=False,
				reason="Missing story title in response payload",
			))
			continue

		try:
			plantuml_text = create_plantuml_syntax(story_json)
		except Exception as exc:
			if output_path.exists():
				output_path.unlink()
			export_statuses.append(ExportStatus(
				story_title=story_title,
				model_name=model_name,
				success=False,
				reason=f"PlantUML generation failed: {exc}",
			))
			continue

		is_valid, failure_reason = validate_plantuml_text(plantuml_text, session=request_session)
		if not is_valid:
			if output_path.exists():
				output_path.unlink()
			export_statuses.append(ExportStatus(
				story_title=story_title,
				model_name=model_name,
				success=False,
				reason=failure_reason,
			))
			continue

		output_path.write_text(plantuml_text, encoding="utf-8")
		export_statuses.append(ExportStatus(
			story_title=story_title,
			model_name=model_name,
			success=True,
			output_path=output_path,
		))

	return export_statuses


if __name__ == "__main__":
	export_statuses = export_promptfoo_results()
	successes = [status for status in export_statuses if status.success]
	failures = [status for status in export_statuses if not status.success]

	print(f"Generated {len(successes)} valid PlantUML files in {OUTPUT_DIR}")
	print(f"Skipped {len(failures)} invalid PlantUML files")

	for status in export_statuses:
		outcome = "✅" if status.success else "❌"
		details = status.output_path.name if status.output_path else status.reason or "Unknown validation error"
		print(f"{outcome} model={status.model_name} | story={status.story_title} | {details}")
