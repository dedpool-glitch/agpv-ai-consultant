from datetime import datetime

from services.conversation_export import build_conversation_markdown


def test_markdown_export_contains_visible_chat_and_simulation_marker():
    messages = [
        {"role": "user", "content": "How does spacing affect yield?"},
        {"role": "assistant", "content": "Wider spacing can reduce shading."},
        {"role": "assistant", "type": "pvmaps_run", "run_index": 0},
        {"role": "assistant", "content": "The estimated annual yield is 1200 kWh."},
    ]
    runs = [{"label": "Solar-yield estimate"}]

    exported = build_conversation_markdown(
        messages, runs, exported_at=datetime(2026, 10, 18, 23, 15)
    )

    assert "Exported: 2026-10-18 23:15" in exported
    assert "## You\n\nHow does spacing affect yield?" in exported
    assert "## AgPV Assistant\n\nWider spacing can reduce shading." in exported
    assert "## PVMAPS result: Solar-yield estimate" in exported
    assert "The estimated annual yield is 1200 kWh." in exported


def test_export_ignores_hidden_fields_and_non_text_messages():
    messages = [
        {
            "role": "user",
            "content": "Visible question",
            "api_key": "secret-key-must-not-appear",
            "internal_trace": {"prompt": "hidden"},
        },
        {"role": "assistant", "content": {"plot": "binary data"}},
        {"role": "system", "content": "System details are not chat messages"},
    ]

    exported = build_conversation_markdown(
        messages, exported_at=datetime(2026, 10, 18, 23, 15)
    )

    assert "Visible question" in exported
    assert "secret-key-must-not-appear" not in exported
    assert "internal_trace" not in exported
    assert "binary data" not in exported
    assert "System details" not in exported
