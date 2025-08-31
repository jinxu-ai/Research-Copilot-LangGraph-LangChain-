# chains/

This directory contains **LangChain Expression Language (LCEL) chains**.

- `plan.py` — generate a structured research plan from a user question.
- `queries.py` — turn plan into multiple search queries.
- `synthesize.py` — summarize retrieved chunks and output structured notes.
- `judge.py` — decide if more evidence is needed.
- `ranker.py` — score and select top candidate sources.
- `utils.py` — helper functions (deduplication, text joining, etc).

Each chain should be composable and testable on its own.
