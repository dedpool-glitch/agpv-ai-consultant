# Paired RAG Evaluation

`demos/run_rag_ab_evaluation.py` replays logged general questions twice under
matched conditions:

- once without retrieved context;
- once with context retrieved through the app's current RAG route.

Both answers use the same model, temperature, user profile, location, and
preceding conversation history. The output retains the retrieved chunks and
provides blank human-review columns.

## Select cases

In the normalized conversation-log CSV, set `include_for_evaluation` to `yes`
for the questions to replay. If no rows are marked, the script uses the first
unique, error-free `general_question` rows up to `--limit`.

## Run

Activate the project environment and make sure `PURDUE_GENAI_KEY` is available,
then run:

```powershell
python -m demos.run_rag_ab_evaluation `
  "path\to\AgPV_RAG_Evaluation_Dataset.csv" `
  "outputs\rag_ab_results.csv" `
  --limit 10
```

Add `--judge` to request a preliminary LLM rubric score for each pair:

```powershell
python -m demos.run_rag_ab_evaluation `
  "path\to\AgPV_RAG_Evaluation_Dataset.csv" `
  "outputs\rag_ab_results.csv" `
  --limit 10 `
  --judge
```

Without `--judge`, each case normally makes two answer requests plus a router
request when the log has no usable source decision. With `--judge`, it makes
one additional request. Start with a small limit because GenAI Studio rate
limits still apply.

## Review

Score both answers using the human-review columns in the output:

- correctness;
- practical usefulness;
- whether the RAG answer is supported by the retrieved excerpts;
- preferred answer;
- unsupported claims and notes.

`answer_similarity_ratio` only describes how alike the two strings are. It is
not a quality score and must not be used to conclude that RAG helped.

The optional LLM judge is also not ground truth. Use it to prioritize cases for
inspection, then report human-reviewed results separately.

This is a per-turn ablation using the historical context saved in the log. If
earlier assistant messages already contain research-derived information, both
arms receive that same history. A later full-session experiment should replay
entire conversations independently with RAG enabled and disabled.
