# Equation-Aware RAG Evaluation

This experiment compares the existing paper collection with a separate collection
that enables Docling formula enrichment and reranks equation-bearing chunks for
questions that explicitly ask for equations. It does not change the collection
used by the application.

In the equation-aware collection, each recognized formula is stored as its own
`record_type="equation"` record. It contains the extracted equation, page, heading,
and nearby prose, plus a stable `parent_id` pointing to the full explanatory
`record_type="context"` chunk. Retrieval promotes equation records for explicit
math questions and attaches the linked parent text before answer generation.

## 1. Build the equation-aware collection

From the project root, run:

```powershell
.\.venv\Scripts\python.exe -m rag.ingest papers ceed_group_papers_equations_v1 --equation-aware
```

The first run may take longer because Docling may load or download its formula
recognition model. Keep the existing `ceed_group_papers` collection unchanged;
it is the baseline.

## 2. Prepare equation questions

Edit `demos/equation_rag_cases.csv`. Each row can contain:

- `question`: the question sent to both retrieval pipelines.
- `expected_terms`: exact symbols or terms separated by `|`, such as `BG|Y_b|Y_m`.
- `expected_title_contains`: a distinctive part of the correct paper title.
- `expected_page`: the PDF page expected to contain the equation.

Use questions whose correct equation and location you have checked manually in
the PDF. Without this reference information, equation hit rate is useful but does
not establish that the retrieved equation is the correct one.

## 3. Compare retrieval

```powershell
.\.venv\Scripts\python.exe -m demos.compare_equation_rag `
  demos\equation_rag_cases.csv `
  outputs\equation_rag_comparison.csv
```

The output reports equation hit at top-k, first equation rank, expected-term
recall, expected source/page hits, retrieval time, and the retrieved chunks from
both pipelines.

## 4. Compare complete answers

To generate an answer from both retrieved contexts, add `--generate-answers`:

```powershell
.\.venv\Scripts\python.exe -m demos.compare_equation_rag `
  demos\equation_rag_cases.csv `
  outputs\equation_rag_answer_comparison.csv `
  --generate-answers
```

The script uses `PURDUE_GENAI_KEY` when available and otherwise prompts for a key.

## 5. Review the output

For each pair, score the blank human-review columns from 1 to 5:

- Retrieval relevance: are the retrieved chunks about the requested relationship?
- Equation accuracy: does the answer reproduce the source equation without changing notation?
- Explanation quality: are supported variables, units, assumptions, and conditions explained clearly?
- Preferred pipeline: enter `old`, `new`, or `tie`.

Do not count an answer as successful merely because it contains mathematical
notation. The equation must answer the question and agree with the source PDF.
Only switch the application to the new path after it improves accuracy and
relevance without causing unacceptable regressions on ordinary questions.
