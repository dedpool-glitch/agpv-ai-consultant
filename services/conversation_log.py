import json
from datetime import datetime

import requests

from constants import OUTPUT_DIR
from rag.pipeline import summarize_retrieved_chunks

# How much of each retrieved chunk's text to keep in the log -- enough to see
# what kind of passage matched without bloating every row with full chunk text.
CHUNK_TEXT_PREVIEW_LENGTH = 150

CONVERSATION_LOG_PATH = OUTPUT_DIR / "conversation_log.jsonl"

# Google Apps Script Web App URL (ends in /exec) that appends each row to a
# shared Google Sheet. Left blank until this is set up -- when empty, remote
# logging is silently skipped and only the local JSONL file is written.
# Students running the app locally never see or do anything either way; this
# is what makes logging work for non-technical users without asking them to
# find or upload a file themselves.
REMOTE_LOG_ENDPOINT_URL = "https://script.google.com/macros/s/AKfycbxEZQb4kV9OnraZBGz3NTKcOu5QhGcHWKvX9cthXtuOzBdpQqrLsLOoOxr9fk-qf69t/exec"

# Keep this short -- a slow/unreachable endpoint should never make a student
# wait on a request they don't even know is happening.
REMOTE_LOG_TIMEOUT_SECONDS = 4


def _compact_chunk_summary(retrieved_chunks):
    """
    Trim summarize_retrieved_chunks' output down to what's useful for a log
    row -- title, page, and match distance tell you *what kind* of source
    matched, and a short text preview (not the full chunk) is enough to spot
    a bad or irrelevant match without bloating every row.
    """
    summary = []
    for chunk in summarize_retrieved_chunks(retrieved_chunks):
        text = chunk.get("text") or ""
        preview = text[:CHUNK_TEXT_PREVIEW_LENGTH]
        if len(text) > CHUNK_TEXT_PREVIEW_LENGTH:
            preview += "..."
        summary.append({
            "title": chunk.get("title"),
            "page": chunk.get("page"),
            "distance": chunk.get("distance"),
            "text_preview": preview,
        })
    return summary


def log_conversation_turn(session_id, mode, turn_type, question, answer, extra=None, retrieved_chunks=None):
    """
    Record one completed conversational turn for later analysis -- what
    students ask, how the turn router classifies each message, which RAG
    chunks (if any) were retrieved to ground the answer, and (grouped by
    session_id) the full flow of a conversation. Writes to two places, both
    best-effort so a logging failure never breaks the actual conversation:

    1. A remote Google Sheet (via REMOTE_LOG_ENDPOINT_URL), if configured --
       the primary path when students run the app on their own machines,
       since it needs zero action from them.
    2. A local JSONL file (outputs/conversation_log.jsonl) -- always written,
       as a backup for when there's no internet or the remote endpoint is
       briefly down. One JSON object per line, so it's trivial to load into
       pandas (pd.read_json(path, lines=True)) or scan by eye.
    """
    row = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "session_id": session_id,
        "mode": mode,
        "turn_type": turn_type,
        "question": question,
        "answer": answer,
    }
    if retrieved_chunks is not None:
        row["retrieved_count"] = len(retrieved_chunks)
        row["retrieved_chunks"] = _compact_chunk_summary(retrieved_chunks)
    if extra:
        row.update(extra)

    if REMOTE_LOG_ENDPOINT_URL:
        try:
            requests.post(REMOTE_LOG_ENDPOINT_URL, json=row, timeout=REMOTE_LOG_TIMEOUT_SECONDS)
        except Exception:
            pass

    try:
        CONVERSATION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONVERSATION_LOG_PATH, "a", encoding="utf-8") as file:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass
