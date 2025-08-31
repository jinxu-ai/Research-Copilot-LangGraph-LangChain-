# graph/

This directory defines the **LangGraph orchestration**.

- `state.py` — TypedDict and Pydantic models (Sources, Claims, Notes).
- `nodes.py` — node implementations (plan, search, select, read, synthesize, decide, write).
- `build.py` — builds and compiles the graph workflow.

This is where the agentic "plan → search → select → read → synthesize → decide → write" loop is assembled.
