"""Create a readable, user-controlled export of the visible conversation."""

from datetime import datetime

from constants import MESSAGE_TYPE_PVMAPS_RUN


ROLE_LABELS = {
    "user": "You",
    "assistant": "AgPV Assistant",
}


def build_conversation_markdown(messages, pvmaps_runs=None, exported_at=None):
    """Return only user-visible chat content as UTF-8 Markdown text."""
    runs = pvmaps_runs or []
    exported_at = exported_at or datetime.now()
    lines = [
        "# AgPV Assistant conversation",
        "",
        f"Exported: {exported_at.strftime('%Y-%m-%d %H:%M')}",
        "",
    ]

    for message in messages or []:
        if not isinstance(message, dict):
            continue
        if message.get("type") == MESSAGE_TYPE_PVMAPS_RUN:
            run_index = message.get("run_index")
            if isinstance(run_index, int) and 0 <= run_index < len(runs):
                run = runs[run_index]
                label = run.get("label") or f"Simulation {run_index + 1}"
                lines.extend([f"## Simulation result: {label}", ""])
            continue

        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            continue
        role = ROLE_LABELS.get(message.get("role"))
        if role is None:
            continue
        lines.extend([f"## {role}", "", content.strip(), ""])

    return "\n".join(lines).rstrip() + "\n"
