# Context-aware retrieval: demo readiness

Implemented October 18, 2026. Current status: **automated and offline integration checks passed; live model validation pending an available Purdue API key.**

Guided chat now asks its existing source-routing call for an optional standalone retrieval query. Independent questions remain byte-for-byte unchanged when classified standalone. Context-dependent follow-ups may be rewritten using up to six recent user/assistant text messages (1,000 characters each). The current message is excluded from prior history; plots and non-conversation roles are excluded. The original question and conversation still go to answer generation.

Expert follow-up chat uses the same query planning when prior text history exists, while retaining its existing both-collection search. It adds one routing API call for those turns; first-turn expert questions skip that call. Existing simulation explanations are not synthesized into conversation history, so implicit references on the first expert turn remain unchanged.

Malformed or missing query fields use the original question. Ambiguous references also retain the original question rather than guessing; this change does not add a forced clarification UI. An expert planner exception falls back to original-query retrieval. Guided source-routing failures retain the existing behavior of skipping research retrieval; a valid source decision with invalid rewrite fields still retrieves using the original query.

The actual retrieval query and mode are recorded in both chat paths' traces/logs. Set `AGPV_CONTEXTUAL_RAG=false` and restart the app to disable query rewriting (expert planning calls are then skipped). This is a query-rewriting switch, not a replacement for the source router.

## Verification completed

- Full automated suite: **118 passed in 45.30 seconds**, including 18 additional cases covering history boundaries, topic-preserving validation, ambiguous mode, malformed responses, missing history, rollback switch, and expert API failure fallback. These tests validate contracts and error handling with a mocked model; they do not establish semantic classification accuracy.
- The app and changed modules parse successfully.
- Real Chroma integration using the application's `retrieve_for_source('both', ...)`, three chunks per collection: denominator, numerator, and temperature/voltage follow-ups missed their reference source/page with the raw question (0/3), and found it with explicitly authored reference queries (3/3). This tests query usefulness and the database path, not live model rewriting.
- No collection re-ingestion, simulation changes, answer prompt changes, or commits.

## Pending live check

The executable smoke evaluation includes three follow-ups, three independent/topic-switch questions, a first-turn question, and an ambiguous reference. It stores each actual plan and retrieved chunks, plus two generated answers for inspection. Do not call it a live pass until results exist and have been reviewed.

With `PURDUE_GENAI_KEY` available in the repository `.env`, run:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m demos.evaluate_contextual_retrieval --output outputs/contextual_rag_20261018/live_results.json
```

Inspect both semantic relevance and planning latency. The prompt cannot guarantee that a probabilistic model always chooses standalone/contextual correctly. A smoke pass is evidence for these cases, not universal behavior. The earlier standalone equation benchmark remains a separate retrieval evaluation.

