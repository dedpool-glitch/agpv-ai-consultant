# Codebase Walkthrough: One Full User Journey

This traces a single concrete scenario end to end through the actual live code path in
`app.py` — not every branch, just the spine everything else hangs off. The scenario:
a farmer fills out the profile form, gives a location, and asks for a quick solar-yield
estimate.

Read this top to bottom once, then try covering the "what it does" column and recalling
it yourself. Wherever you blank, that's your real reading list — not the whole repo.

## 0. Before any of this: what's live vs. legacy

`app.py` only imports from `llm/`: `consultation_planner`, `general_agpv_answerer`, and
(indirectly, via `services/pvmaps_estimate_service.py`) `candidate_config_validator`,
`output_generator`, `recommended_pvmaps_config`.

`llm/candidate_config_generator.py`, `llm/intent_classifier.py`,
`llm/parameter_extractor.py`, and `llm/question_generator.py` are **not imported by
app.py at all**. They're an earlier field-by-field questionnaire design (ask one
field, classify the answer, extract a value, ask the next field) that got superseded
by the current two-stage design: `consultation_planner` decides *when* enough is known,
`recommended_pvmaps_config` fills in *everything at once* from context. Those four
files are only exercised by the standalone scripts in `demos/` now. Don't spend time
feeling like you need to understand them as part of the live app — they're historical,
not dead weight to delete without checking, but not part of this walkthrough either.

## 1. Profile form — `app.py`

The very first block in `app.py` (`if "user_profile" not in st.session_state`) renders
a Streamlit form: user type, role details, solar experience, project goal, goal
details, site location text box, optional datasheet upload.

On submit, if a location was typed, it calls:

```
services/location_geocoder.py -> geocode_location(site_location)
```

which turns free text like "Lafayette, Indiana" into a confirmed address + lat/lon.
That result becomes `st.session_state["location_context"]`. The form's other answers
become `st.session_state["user_profile"]` — a plain dict, not validated against any
schema at this point (validation happens later, downstream, against the PVMAPS input,
not against what the user typed here).

Then it calls `start_consultation(location_context)` and reruns the page.

## 2. The consultation loop — `start_consultation` in `app.py` + `llm/consultation_planner.py`

`start_consultation` calls:

```
llm/consultation_planner.py -> plan_next_consultation_step(
    api_key, user_profile, location_context, consultation_history
)
```

This sends one LLM call asking, in effect: "given what we know so far, do we have
enough to attempt a PVMAPS estimate, or should we ask one more question?" The response
is parsed into `{"question", "known_facts", "reason", "ready_for_pvmaps"}`.

- If `ready_for_pvmaps` is `False`: the planner's `question` gets shown in a
  chat-style loop (`goal_follow_up_messages`). Each time the user answers, their answer
  is appended to **both** `goal_follow_up_messages` (what's displayed) and
  `consultation_messages` (the structured history sent back into the planner next
  time). The planner runs again with the growing history until it says
  `ready_for_pvmaps = True`.
- If `ready_for_pvmaps` is `True` (sometimes immediately, if the user's first message
  already gave enough): it sets `post_consultation_route = "general_chat"` and calls
  `run_recommended_pvmaps_estimate` right away.

**Why this exists as a separate step from general chat:** it's the only place that
builds a real `consultation_messages` history before ever asking for a PVMAPS
recommendation. (This is also the exact mechanism that broke when RAG routing was
added directly into `general_chat` and this loop got deleted — see the debugging
session from earlier for the full story. It's back now, intact.)

## 3. Generating the recommendation — `services/pvmaps_estimate_service.py`

`run_recommended_pvmaps_estimate(session_state, api_key, location_context)` is the
orchestrator for everything from "we have enough context" to "here's a finished
estimate or a clear failure." In order:

1. Bails out early with a chat message if `lat`/`lon` are missing — no point calling
   an LLM for a config with no coordinates.
2. Builds `consultation_history` from three lists: `consultation_messages`,
   `general_chat_messages`, `post_result_messages`.
3. Calls `llm/recommended_pvmaps_config.py -> generate_recommended_pvmaps_config(...)`,
   which sends **one big LLM call** with the user profile, location, full
   consultation history, current (mostly-null) PVMAPS state, and the allowed field
   schema, asking the model to propose values for every missing field plus a short
   justification for each. The response is expected to be raw JSON shaped like
   `{"pvmaps_inputs": {...8 fields...}, "justifications": {...}}`.
4. Passes that straight into `llm/candidate_config_validator.py ->
   validate_candidate_config(candidate)`, which checks `pvmaps_inputs` exists, then
   runs each of the 8 required fields through
   `questionnaire/parser.py -> parse_questionnaire_answer` (type/range coercion per
   field). Any missing field or parse error becomes a validation error string.
5. Logs all of this via `services/llm_trace.py -> add_llm_trace(...)` — this is the
   sidebar trace panel you've been reading during debugging. Every major decision
   point in the app logs through this one function; it's worth knowing it exists
   everywhere, not just here.
6. **If validation failed:** appends the "did not pass validation yet" chat message
   and stops. (This is the exact failure mode from the debugging session — a
   `recommendation_failed` decision here, either from thin context or, as it turned
   out, the model returning a tool call instead of the requested JSON.)
7. **If validation passed:** merges the recommended values into
   `questionnaire/state.py`'s state dict (only overwriting fields that were still
   `None`, via `update_questionnaire_state(..., assumed=True)`), then:
   - `questionnaire/to_pvmaps.py -> build_pvmaps_input_from_questionnaire(state, lat, lon)`
     resolves panel specs (via `services/panel_specs.py`, or hardcoded defaults if
     `panel_model == "default values"`) and shapes everything into the nested dict
     PVMAPS itself expects (`module.*`, `array.*`, `lat`, `lon`).
   - `pvmaps/input_validator.py -> validate_pvmaps_input(pvmaps_input)` runs a second,
     independent set of checks — physical/numeric bounds this time (efficiency
     ranges, tilt range, albedo range, the `elevation > module height / 2` clearance
     rule), not the LLM-facing field checks from step 4. **This is the deliberate
     "don't trust the LLM, verify the physics" gate** — the whole reason a
     conversational LLM is allowed anywhere near a MATLAB simulator at all.
   - If that passes: `pvmaps/matlab_runner.py -> run_pvmaps(pvmaps_input, script_path)`
     starts a MATLAB engine, pushes every field into a MATLAB `input` struct via
     `eng.eval(...)`, and calls the actual `simulate()` function from the PVMAPS
     MATLAB codebase, returning yearly/monthly/daily yield.
   - `llm/output_generator.py -> explain_output(output, api_key, user_profile)` sends
     one more LLM call to turn the raw numeric output into a plain-language
     explanation for a non-expert.
   - The explanation and a `"type": "latest_estimate"` marker get appended to
     `general_chat_messages`, which is what triggers the chart-rendering block back
     in `app.py`'s render loop.

## 4. General chat, after the estimate — back in `app.py`

Once `post_consultation_route == "general_chat"`, every subsequent user message goes
through `llm/general_agpv_answerer.py -> answer_general_agpv_question(...)`, which
gets the question, profile, location, current questionnaire state, the latest PVMAPS
output (if any), and the full conversation history, and returns a plain-language
answer. Each turn also re-checks `plan_next_consultation_step` — the same planner
from step 2 — in case a **later** message reveals enough new information to attempt
PVMAPS again (relevant if the first pass never reached `ready_for_pvmaps`, or if you're
using this loop as the entry point when RAG routing exists — see below).

## 5. Where RAG fits in (currently unwired)

`rag/` is a complete, separately-working pipeline — `document_loader.py` (Docling PDF
parsing), `chunker.py` (HybridChunker, tokenizer-aware, structure-aware chunking),
`vector_db.py` (Chroma collection helpers), `rag_answerer.py` (formats retrieved
chunks into a prompt and answers from them only). The `ceed_group_papers` Chroma
collection already exists and is populated (804 chunks). None of this is currently
called from `app.py` — the previous attempt to wire it in via a `message_router`
accidentally deleted the step-2 consultation loop in the process, and separately hit a
model-side tool-calling issue unrelated to the wiring itself. Both are understood now;
re-wiring it properly (without touching step 2, and with a guard against tool-call-
shaped LLM responses) is a discrete next task, not something this walkthrough covers.

## Self-check

Before moving to any other file in the repo, try narrating steps 1 through 4 above out
loud, from memory, using only function names (not this document). Then pick one thing
you got fuzzy on and go reread *only* that file. That's a better use of an hour than
reading every file in `services/` and `pvmaps/` in alphabetical order.
