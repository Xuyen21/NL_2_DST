import re
from pathlib import Path
from statistics import median

from utils.promptfoo_result_utils import extract_prompting_mode, load_provider_models
from verification import load_json


REPORT_PATH = Path(__file__).resolve().parent / "results-zero-shot-cot-gpt-flash.json"
PROMPTFOO_CONFIG_PATH = Path(__file__).resolve().parent / "promptfoo_eval" / "promptfooconfig_pilot.yaml"

def format_provider_name(label: str) -> str:
    first_token = label.split()[0]
    match = re.match(r"[A-Za-z]+", first_token)
    base_name = match.group(0) if match else first_token

    if base_name.upper() in {"GPT", "GLM"}:
        return base_name.upper()

    return base_name.capitalize()


def load_promptfoo_providers(config_path: Path) -> list[dict[str, str]]:
    provider_models = load_provider_models(config_path)
    return [
        {
            "id": provider_id,
            "label": model_name,
        }
        for provider_id, model_name in provider_models.items()
    ]


class CalculateFinalMetrics:
    def __init__(self, report: list[dict], provider_id: str):
        self.report = report
        self.individual_model = provider_id

    def _iter_provider_results(self):
        for result in self.report:
            provider = result.get("provider", {})
            if provider.get("id") == self.individual_model:
                yield result

    def _iter_component_results(self):
        for result in self._iter_provider_results():
            grading_result = result.get("gradingResult")
            if grading_result is None:
                continue
            component_results = grading_result.get("componentResults", [])

            if component_results:
                yield component_results[0]

    def get_model_pass_rate(self):
        total_fields = 0
        correct_fields = 0

        for component in self._iter_component_results():
            total_fields += component.get("total_fields", 0)
            correct_fields += component.get("correct_fields", 0)

        pass_rate = correct_fields / total_fields if total_fields else 0
        rounded_pass_rate = round(pass_rate, 2)

        return {
            "total_fields": total_fields,
            "correct_fields": correct_fields,
            "pass_rate": rounded_pass_rate,
        }

    def _f1(self, corrects: int, missings: int, hallu: int) -> float:
        precision_den = corrects + hallu
        recall_den = corrects + missings

        precision = corrects / precision_den if precision_den else 0.0
        recall = corrects / recall_den if recall_den else 0.0

        if precision + recall == 0:
            return 0.0

        f1_score = round(2 * precision * recall / (precision + recall), 2)

        return f1_score

    def get_model_F1_scores(self):
        actors_corrects = actors_missings = actors_hallu = 0
        work_corrects = work_missings = work_hallu = 0
        activities_corrects = activities_missings = activities_hallu = 0

        for component in self._iter_component_results():
            actors = component.get("actors_result", {})
            actors_corrects += actors.get("corrects", 0)
            actors_missings += actors.get("missings", 0)
            actors_hallu += actors.get("hallu", 0)

            work_objects = component.get("work_objects_result", {})
            work_corrects += work_objects.get("corrects", 0)
            work_missings += work_objects.get("missings", 0)
            work_hallu += work_objects.get("hallu", 0)

            activities = component.get("activities_result", {})
            activities_corrects += activities.get("corrects", 0)
            activities_missings += activities.get("missings", 0)
            activities_hallu += activities.get("hallu", 0)

        return {
            "actors_f1": self._f1(actors_corrects, actors_missings, actors_hallu),
            "work_objects_f1": self._f1(work_corrects, work_missings, work_hallu),
            "activities_f1": self._f1(
                activities_corrects, activities_missings, activities_hallu
            ),
        }

    def get_model_p50_latency(self):
        latencies = self.get_model_latencies()

        p50_latency_seconds = round(median(latencies) / 1000, 2) if latencies else 0

        return {
            "num_samples": len(latencies),
            "p50_latency_seconds": p50_latency_seconds,
        }

    def get_model_latencies(self) -> list[int]:
        latencies = []

        for result in self._iter_provider_results():
            latency_ms = result.get("latencyMs")
            if latency_ms is not None:
                latencies.append(latency_ms)

        return sorted(latencies)


if __name__ == "__main__":
    report = load_json(REPORT_PATH)
    results_list = report["results"]["results"]
    provider_configs = load_promptfoo_providers(PROMPTFOO_CONFIG_PATH)

    metrics_by_provider = []
    for provider_config in provider_configs:
        model_name = format_provider_name(provider_config["label"])
        prompting_mode = extract_prompting_mode(provider_config["id"])
        display_name = f"{model_name} ({prompting_mode})"
        metrics_by_provider.append(
            {
                "name": display_name,
                "label": provider_config["label"],
                "prompting_mode": prompting_mode,
                "metrics": CalculateFinalMetrics(results_list, provider_config["id"]),
            }
        )

    for provider in metrics_by_provider:
        print(f"{provider['name']} Final Results:", provider["metrics"].get_model_pass_rate())
    print("------------------------------")

    for provider in metrics_by_provider:
        print(f"{provider['name']} F1 Scores:", provider["metrics"].get_model_F1_scores())
    print("------------------------------")

    for provider in metrics_by_provider:
        model_metrics = provider["metrics"]
        latencies = model_metrics.get_model_latencies()

        print(f"{provider['name']} P50 Latency:", model_metrics.get_model_p50_latency())
        print(f"{provider['name']} latencies (ms):", latencies)
        print(f"{provider['name']} latencies (s):", [round(ms / 1000, 2) for ms in latencies])
