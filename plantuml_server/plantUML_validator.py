from pathlib import Path
from typing import Any
import html
import re
import time
import requests


LINE_HEADER_PATTERN = re.compile(r"\[From string \(line\s+(\d+)\)\s*\]", re.IGNORECASE)


def _extract_svg_text(svg_text: str) -> list[str]:
    texts = re.findall(r"<text\b[^>]*>(.*?)</text>", svg_text, flags=re.DOTALL | re.IGNORECASE)
    cleaned = []

    for t in texts:
        t = re.sub(r"<[^>]+>", "", t)
        t = html.unescape(t)
        t = re.sub(r"\s+", " ", t).strip()
        if t:
            cleaned.append(t)

    return cleaned


def _extract_error_focus(text_lines: list[str]) -> dict[str, Any]:
    """
    Extract only:
    - displayed line number from '[From string (line X)]'
    - the most likely offending source line

    Heuristic:
    - line number comes from the explicit PlantUML error header in SVG text
    - offending content is taken as the last non-meta line
    """
    error_line = None
    error_content = None

    for line in text_lines:
        m = LINE_HEADER_PATTERN.search(line)
        if m:
            error_line = int(m.group(1))
            break

    meta_prefixes = (
        "[from string",
        "@startuml",
        "syntax error",
        "... ( skipping",
    )

    candidates = []
    for line in text_lines:
        low = line.lower()
        if low.startswith(meta_prefixes):
            continue
        if "assumed diagram type" in low:
            continue
        candidates.append(line)

    if candidates:
        error_content = candidates[-1]

    return {
        "error_line": error_line,
        "error_content": error_content,
    }


def validate_plantuml_text(
    puml_text: str,
    server_url: str = "http://localhost:8080",
    endpoint: str = "/svg",
    timeout: int = 1,
) -> dict[str, Any]:
    start_time = time.perf_counter()
    url = f"{server_url.rstrip('/')}{endpoint}"

    try:
        response = requests.post(
            url,
            data=puml_text.encode("utf-8"),
            headers={"Content-Type": "text/plain; charset=utf-8"},
            timeout=timeout,
        )
    except requests.RequestException as e:
        runtime_seconds = time.perf_counter() - start_time
        return {
            "ok": False,
            "status_code": None,
            "error_message": f"Could not reach PlantUML server: {e}",
            "error_line": None,
            "error_content": None,
            "runtime_seconds": round(runtime_seconds, 4),
        }

    headers = dict(response.headers)
    error_message = headers.get("X-PlantUML-Diagram-Error")


    error_line = None
    error_content = None

    content_type = headers.get("Content-Type", "")
    if "svg" in content_type.lower() or response.text.lstrip().startswith("<svg"):
        svg_lines = _extract_svg_text(response.text)

        if svg_lines:
            focus = _extract_error_focus(svg_lines)
            error_line = focus["error_line"]
            error_content = focus["error_content"]

    runtime_seconds = time.perf_counter() - start_time

    if error_message:
        return {
            "ok": False,
            "status_code": response.status_code,
            "error_message": error_message,
            "error_line": error_line,
            "error_content": error_content,
            "runtime_seconds": round(runtime_seconds, 4),
        }

    if response.status_code >= 400:
        return {
            "ok": False,
            "status_code": response.status_code,
            "error_message": f"PlantUML server returned HTTP {response.status_code}",
            "error_line": error_line,
            "error_content": error_content,
            "runtime_seconds": round(runtime_seconds, 4),
        }

    return {
        "ok": True,
        "status_code": response.status_code,
        "error_message": None,
        "error_line": None,
        "error_content": None,
        "runtime_seconds": round(runtime_seconds, 4),
    }


def validate_plantuml_file(
    puml_file: str | Path,
    server_url: str = "http://localhost:8080",
    endpoint: str = "/svg",
    timeout: int = 1,
) -> dict[str, Any]:
    start_time = time.perf_counter()
    puml_file = Path(puml_file)

    if not puml_file.exists():
        runtime_seconds = time.perf_counter() - start_time
        return {
            "ok": False,
            "status_code": None,
            "error_message": f"PUML file not found: {puml_file}",
            "error_line": None,
            "error_content": None,
            "runtime_seconds": round(runtime_seconds, 4),
        }

    puml_text = puml_file.read_text(encoding="utf-8")
    result = validate_plantuml_text(
        puml_text=puml_text,
        server_url=server_url,
        endpoint=endpoint,
        timeout=timeout,
    )

    total_runtime_seconds = time.perf_counter() - start_time
    result["total_runtime_seconds"] = round(total_runtime_seconds, 4)
    return result




if __name__ == "__main__":
    test_file = r"C:\code\NL_2_DST\presentation_story.puml"   #r"C:\code\NL_2_DST\alphorn_plantUML\alphorn-2-riskassessment.puml" r"C:\code\NL_2_DST\alphorn_plantUML\alphorn-1-standardcase.puml"
    result = validate_plantuml_file(test_file)

    print("ok:", result["ok"])
    print("status_code:", result["status_code"])

    print("error_message:", result["error_message"])
    print("error_line:", result["error_line"])
    print("error_content:", result["error_content"])
    print("server_runtime_seconds:", result["runtime_seconds"])
    print("total_runtime_seconds:", result["total_runtime_seconds"])


