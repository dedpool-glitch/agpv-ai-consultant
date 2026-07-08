from datetime import datetime


def add_llm_trace(session_state, stage, input_summary=None, output=None, decision=None):
    session_state.setdefault("llm_trace", [])
    session_state["llm_trace"].append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "stage": stage,
        "input": input_summary,
        "output": output,
        "decision": decision,
    })
