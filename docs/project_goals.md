# Project Goals

This document captures the current goals and engineering requirements for the
AgPV Assistant prototype.

## Current Scope

The system should support a natural AgPV planning conversation. The assistant
should be able to answer research-backed questions from CEED papers, run
PVMAPS when a solar-yield estimate is useful, and continue the conversation
after model output is available.

The key product shift is:

```text
old framing: conversation -> eventually run PVMAPS
new framing: conversation -> choose the right tool when needed
```

PVMAPS is the first scientific backend model. RAG over CEED papers is the first
knowledge-grounding tool.

## Mandatory Requirements

### User Flow

- The user must be able to provide a profile/background.
- The user may provide a site location when site-specific analysis is needed.
- The app should support open-ended AgPV conversation.
- The app should not force every conversation toward PVMAPS.
- The user should be able to ask follow-up questions after a model result.

### Routing

- The app should include a routing step before deciding how to answer a user
  message.
- The first router version may be simple and should distinguish:
  - paper/RAG questions
  - existing PVMAPS/general flow
- The router should be visible in the LLM trace or other debug output.
- RAG should not be called for every message.

### RAG

- CEED papers should be loaded from a local resource folder.
- PDFs should be parsed with Docling.
- Chunks should preserve useful metadata such as title, page, source, and
  headings.
- Chunks should be stored in ChromaDB.
- RAG answers should use retrieved excerpts only.
- RAG answers should include source metadata when possible.
- Local PDFs and Chroma DB files should not be committed.

### PVMAPS

- The app must validate PVMAPS inputs before MATLAB runs.
- The LLM must not bypass deterministic validation.
- PVMAPS output must be converted into a Python-readable structure.
- PVMAPS output explanations must use validated model outputs and explicit
  assumptions.
- PVMAPS should be treated as one backend tool, not the only purpose of the
  application.

### LLM Safety

- The LLM should not invent scientific values, citations, or simulation output.
- The LLM may phrase questions, rewrite queries, route requests, and explain
  validated outputs.
- The backend should own validation, defaults, state, and model execution.
- RAG answers must say when the retrieved sources do not answer the question.

## Advisory Requirements

### Code Organization

- Keep static labels, options, and validation messages in `constants.py`.
- Keep LLM prompts in `llm/prompts.py`.
- Keep RAG document loading, chunking, retrieval, and answering in `rag/`.
- Keep model-specific code in model packages such as `pvmaps/`.
- Keep app orchestration thin and avoid putting tool logic directly in
  `app.py`.
- Keep demo scripts in `demos/`.

### RAG Evaluation

- Use a small set of profile-specific questions to evaluate answer quality.
- Save demo answers and sources to CSV for meeting review.
- Check whether retrieved chunks actually support the answer.
- Add query rewriting only if natural user questions retrieve weak results.

### Future Simulation Design

- Store model outputs as a list of simulation runs, not only as one latest
  result.
- Support multiple PVMAPS scenarios in one consultation.
- Keep quick ML solar-yield estimates as a separate model/tool from PVMAPS.

## Future Requirements

### Multiple Knowledge Bases

Books, lecture pages, and video transcripts should not be mixed blindly into
the CEED paper collection. They should be added as separate collections.

Possible collections:

```text
ceed_papers
solar_books
lecture_pages
video_transcripts
```

Later routing can choose the correct collection based on user intent.

### Multiple Models

Future model tools may include:

```text
PVMAPS detailed solar-yield simulation
quick ML solar-yield estimator
SIMPLE crop-yield model
scenario comparison tools
```

### Datasheet Extraction

- Allow users to upload a solar panel datasheet.
- Extract panel specs into a structured dictionary.
- Validate extracted specs before using them in PVMAPS.
- Store extracted specs separately from the original upload.

## Current Non-Goals

- The app does not yet optimize a complete AgPV design.
- The app does not yet predict crop yield.
- The app does not yet perform economic analysis.
- The app does not yet route across books, lectures, and papers.
- The app does not yet support multiple PVMAPS runs in one conversation.
- The app does not yet integrate the quick ML solar-yield model.
