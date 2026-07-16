from statistics import median

from verification import load_json


class CalculateFinalMetrics:
    def __init__(self, report: list[dict], provider_id: str):
        self.report = report
        self.individual_model = provider_id

    def get_model_pass_rate(self):
        total_fields = 0
        correct_fields = 0

        for result in self.report:
            provider = result.get("provider", {})
            if provider.get("id") != self.individual_model:
                continue

            component_results = result.get("gradingResult", {}).get(
                "componentResults", []
            )

            if not component_results:
                continue

            component = component_results[0]
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

        for result in self.report:
            provider = result.get("provider", {})
            if provider.get("id") != self.individual_model:
                continue

            component_results = result.get("gradingResult", {}).get(
                "componentResults", []
            )
            if not component_results:
                continue

            component = component_results[0]

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
        latencies = []

        for result in self.report:
            provider = result.get("provider", {})
            if provider.get("id") != self.individual_model:
                continue

            latency_ms = result.get("latencyMs")
            if latency_ms is None:
                continue

            latencies.append(latency_ms)

        p50_latency_seconds = round(median(latencies) / 1000, 2) if latencies else 0

        return {
            "num_samples": len(latencies),
            "p50_latency_seconds": p50_latency_seconds,
        }


if __name__ == "__main__":
    report_path = r"C:\code\NL_2_DST\evaluations\results-zero-shot-qwenmax.json"
    report = load_json(report_path)
    results_list = report["results"]["results"]

    gpt_id = "file://provider_requests.py:one_phase_zeroshot_gpt"
    claude_id = "file://provider_requests.py:one_phase_zeroshot_claude"
    gemini_id = "file://provider_requests.py:one_phase_zeroshot_gemini"

    gpt_metrics = CalculateFinalMetrics(results_list, gpt_id)
    claude_metrics = CalculateFinalMetrics(results_list, claude_id)
    gemini_metrics = CalculateFinalMetrics(results_list, gemini_id)

    gpt_final_results = gpt_metrics.get_model_pass_rate()
    gemini_final_results = gemini_metrics.get_model_pass_rate()
    claude_final_results = claude_metrics.get_model_pass_rate()

    print("GPT Final Results:", gpt_final_results)
    print("GEMINI Final Results:", gemini_final_results)
    print("Claude Final Results:", claude_final_results)
    print("------------------------------")

    gpt_f1_scores = gpt_metrics.get_model_F1_scores()
    gemini_f1_scores = gemini_metrics.get_model_F1_scores()
    claude_f1_scores = claude_metrics.get_model_F1_scores()

    print("GPT F1 Scores:", gpt_f1_scores)
    print("GEMINI F1 Scores:", gemini_f1_scores)
    print("Claude F1 Scores:", claude_f1_scores)
    print("------------------------------")

    gpt_p50_latency = gpt_metrics.get_model_p50_latency()
    gemini_p50_latency = gemini_metrics.get_model_p50_latency()
    claude_p50_latency = claude_metrics.get_model_p50_latency()

    print("GPT P50 Latency:", gpt_p50_latency)
    print("GEMINI P50 Latency:", gemini_p50_latency)
    print("Claude P50 Latency:", claude_p50_latency)

    gemini_id = "file://provider_requests.py:one_phase_zeroshot_gemini"

    gemini_latencies = sorted(
        result["latencyMs"]
        for result in results_list
        if result.get("provider", {}).get("id") == gemini_id
        and result.get("latencyMs") is not None
    )

    print("Gemini latencies (ms):", gemini_latencies)
    print("Gemini latencies (s):", [round(ms / 1000, 2) for ms in gemini_latencies])