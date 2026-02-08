import json
import sys
from pathlib import Path


def q(s: str) -> str:
    """Quote a PlantUML string safely."""
    # PlantUML strings are typically in double quotes; escape internal quotes.
    return '"' + s.replace('"', '\\"') + '"'


def render_actor(a: dict) -> str:
    """
    Render an actor definition.
    Expected types: Person | System (you can extend this).
    """
    a_type = a.get("type", "Person")
    name = a["name"]
    label = a.get("label", "")
    tag = a.get("tag", "")
    note = a.get("note", "")

    # DomainStory-PlantUML macros typically look like:
    # Person("id", "Label")
    # System("id", "Label")
    # If your included domainStory.puml uses different macros, adjust here.
    if a_type not in {"Person", "System"}:
        raise ValueError(f"Unsupported actor type: {a_type}")

    # First argument: internal id in diagram (we use the JSON id)
    # Second argument: label shown on diagram (fall back to name)
    shown = label if label else name

    # Some DomainStory-PlantUML variants accept more args; keep it minimal & robust.
    return f'{a_type}({q(a["id"])}, {q(shown)})'


def render_work_object(o: dict) -> str:
    """
    Render a work object definition.
    Expected types: Document | Object (you can extend).
    """
    o_type = o.get("type", "Object")
    name = o["name"]
    label = o.get("label", "")

    shown = label if label else name

    # Many DomainStory-PlantUML templates provide:
    # Document("id", "Label")
    # Object("id", "Label")
    if o_type == "Document":
        return f'Document({q(o["id"])}, {q(shown)})'
    if o_type == "Object":
        return f'Object({q(o["id"])}, {q(shown)})'

    raise ValueError(f"Unsupported workObject type: {o_type}")


def resolve_ref(ref: str, ids: set) -> str:
    """
    If ref is a known id, emit it as an identifier (unquoted).
    If it's not a known id (e.g., "offer"), emit it as a quoted string.
    """
    if ref in ids:
        return ref  # PlantUML identifier
    return q(ref)  # literal word/phrase


def render_activity(step: dict, known_ids: set) -> str:
    """
    Render activity(...) call.

    Template (common):
    activity($step, $subject, $predicate, $object[, $post][, $target] ...)
    We'll emit: activity(marker, subject, predicate, object, post, target)
    Only include post/target if present.
    """
    marker = step.get("marker", "_")
    subject = resolve_ref(step["subject"], known_ids)
    predicate = q(step["predicate"])
    obj = resolve_ref(step["object"], known_ids)

    parts = [resolve_ref(marker, known_ids), subject, predicate, obj]

    post = step.get("post")
    target = step.get("target")

    if post is not None:
        parts.append(q(post))
        if target is not None:
            parts.append(resolve_ref(target, known_ids))
    elif target is not None:
        # if target provided without post, we still add it but it's unusual
        parts.append(resolve_ref(target, known_ids))

    return f"activity({', '.join(parts)})"


def convert(json_path: Path, out_path: Path) -> None:
    data = json.loads(json_path.read_text(encoding="utf-8"))

    title = data.get("title", "Domain Story")
    include = data.get(
        "include",
        "https://raw.githubusercontent.com/johthor/DomainStory-PlantUML/main/domainStory.puml",
    )

    actors = data.get("actors", [])
    work_objects = data.get("workObjects", [])
    activities = sorted(data.get("activities", []), key=lambda x: x.get("seq", 0))

    # IDs used as PlantUML identifiers
    known_ids = {a["id"] for a in actors} | {o["id"] for o in work_objects}

    lines = []
    lines.append("@startuml")
    lines.append(f"!include {include}")
    lines.append("")
    lines.append(f"title {title}")
    lines.append("")
    lines.append("' Actors")
    for a in actors:
        lines.append(render_actor(a))
    lines.append("")
    lines.append("' Work Objects")
    for o in work_objects:
        lines.append(render_work_object(o))
    lines.append("")
    lines.append("' Activities")
    for step in activities:
        lines.append(render_activity(step, known_ids))
    lines.append("")
    lines.append("@enduml")

    out_path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    # Usage:
    #   python json_to_domainstory.py story.json story.puml
    if len(sys.argv) < 2:
        print("Usage: python json_to_domainstory.py <input.json> [output.puml]")
        sys.exit(1)

    in_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2]) if len(sys.argv) >= 3 else in_path.with_suffix(".puml")

    convert(in_path, out_path)
    print(f"Wrote: {out_path}")
