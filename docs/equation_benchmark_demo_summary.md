# Equation-aware RAG: expanded demo evaluation

Evaluated October 18, 2026 against `data/chroma_db/`, repository HEAD `1b44045337af89a8bab591d839c9c174d9e28e5b`. Retrieval-only evaluation; no generated-answer or MATLAB claims.

**Demo statement:** On 18 paper and 14 book questions grounded in stored equations, equation-aware retrieval improved equation presence, expected-term recall, and equation ranking. It still misses requested formulas on some questions; equation presence is not equation correctness.

| Metric at top 5 | Papers old → new | Books old → new |
|---|---:|---:|
| Any equation signal hit | 77.8% → 94.4% (14 → 17 / 18) | 92.9% → 100% (13 → 14 / 14) |
| Mean expected-term recall | 28.2% → 73.1% | 30.5% → 93.9% |
| Expected source hit | 94.4% → 100% | 100% → 100% |
| Expected source AND page hit | 72.2% → 72.2% (13 / 18) | 64.3% → 71.4% (9 → 10 / 14) |
| Mean first equation rank, when found | 2.64 → 1.35 | 1.77 → 1.00 |
| Equation reciprocal rank, misses = 0 | 0.426 → 0.819 | 0.679 → 1.000 |
| Mean retrieval latency, warm (ms) | 150.1 → 155.9 | 156.1 → 156.7 |
| Median retrieval latency, warm (ms) | 147.0 → 155.5 | 157.0 → 158.5 |

The legacy page-only metric happens to equal the joint source/page metric in this run. The added joint metric prevents a page from another source from counting as a hit.

## Coverage and verification

Papers: nine sources, one to three questions each. Three Critical Analysis; three Khan 2017; three Patel 2019; two rice/agrivoltaics; two Khan 2021 review; two Patel 2023 tandem; one each PGML 2025, Re-thinking LCOE, and Patel 2020. Topics include bifacial gain, diffuse and ground irradiance, masking/shadow geometry, annual yield, land productivity, discounting/degradation, LCOE and optimization, temperature, and tandem electrical behavior.

Books: 11 alam book cases and three solar cells excerpt cases, spanning stored pages 24–451. This is source-diversified, not equal-source balanced: only five equation records exist in the excerpt, and the remaining two are a closely related attenuation expression and a noisy spectral expression. The selection preserves the original eight book questions and adds six distinct concepts rather than padding the small source with near-duplicates. Alam book accounts for 718/723 stored equations; the excerpt is deliberately oversampled relative to its inventory share.

All 32 cases were selected before running the comparison. Each has a stable stored record ID, title, page, concept, exact extracted formula, surrounding explanation, and linked parent saved in `verified_equation_evidence.json`. Expected terms were checked against those stored documents. Some records contain OCR noise (for example, the tandem voltage label and duplicated temperature-yield formula); this is explicitly a stored-record grounding audit, not independent verification against PDF page images. Avoid displaying noisy extraction as a validated scientific transcription.

The original questions remain unchanged. References now use full stored titles, and book term spelling was aligned with the stored representation. No questions were rewritten or removed after observing failures. No app features or retrieval settings were changed.

## Failure review and demo implications

- **Real paper retrieval misses:** paper_002 (diffuse decomposition), _006 (PGML inputs), _007 (GHI decomposition), _009 (masking angles), _010 (annual yield sum), _015 (fractional LCOE tradeoff), and _016 (temperature-dependent integral). Some still score an equation hit because a different formula or mathematical symbol is present. Title and reference matches can displace useful content.
- **Source/page does not prove formula success:** paper_006 and _007 find the right page without the requested formula. paper_012 finds an equivalent discounted-energy equation in Patel 2019 at rank 4, rather than the target expression from Re-thinking LCOE.
- **Book page misses with useful content:** book_001 retrieves the same GHI relationship on p262 instead of p31. book_002 retrieves the air-mass relationship inside explanatory text on p262 rather than p30. These remain strict page misses; no post-hoc ground-truth changes were made.
- **Real book misses:** book_012 retrieves a simplified LCOE example that omits the requested costs/rates; book_014 retrieves shunt-loss and I-V equations instead of the combined fill-factor expression.
- **Earlier pilot:** the first three paper cases still score 2/3 old and 3/3 new on *any-equation* hit, consistent with the earlier headline. However, paper_002 has zero expected-term recall and misses the target page in the new run. The earlier 100% must not be presented as correct-equation retrieval accuracy.

For a rehearsed retrieval demonstration, suitable examples from this run are paper_001 (bifacial gain), paper_005 (ground irradiance integration), paper_018 (temperature coefficients), book_004 (distance/intensity), and book_011 (heating/voltage). These are selected examples, not evidence of universal reliability. Generated answers and the app's combined papers/books path were not tested here, so these are not end-to-end demo guarantees.

## Method and reproducibility

The existing `compare_equation_rag.evaluate_case` evaluates standard old-collection retrieval versus equation-aware new-collection retrieval with k=5 and 20 candidates. Each collection pair was warmed with one unrelated irradiance query; the excluded warm-up took 3.10 seconds for papers and 0.39 seconds for books. Each case was then timed once, old followed by new. Latencies include collection access and, for new retrieval, reranking and parent attachment. They are descriptive measurements, not statistically established speed differences; initialization and fixed order can affect them.

Expected-term recall is the existing whitespace/brace-normalized substring proxy over top-five chunk text. It can pool terms across unrelated chunks, match generic symbols, and penalize alternative notation. Separate attached parent text is exported but is not included in that legacy recall calculation. Any-equation hit uses metadata or heuristic mathematical signals; rank refers to the first such signal, not the requested formula. Do not label these metrics answer accuracy. Human-review fields remain blank; `agent_retrieval_review.csv` identifies the reviewer as Codex.

Run from the repository:

```powershell
.\.venv\Scripts\python.exe -m demos.run_balanced_equation_eval --output-dir outputs/equation_balanced_20261018_rerun
```

The expanded CSVs also work directly with `demos/compare_equation_rag.py`; extra provenance columns are ignored by that original script. Results and evidence are saved under `outputs/equation_balanced_20261018/`. The reusable runner and this summary are evaluation-only additions. No new full-suite run is claimed; the previously reported 98-test pass remains the development-freeze baseline. Neither virtual environment nor either database directory is included in the evaluation deliverables. No commit was created.
