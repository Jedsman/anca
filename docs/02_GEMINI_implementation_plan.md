# Implementation Plan: Editor-in-Chief Architecture

We are pivoting from a linear workflow to a **Hierarchical Map-Reduce** architecture to solve the length and quality issues.

## User Review Required

> [!IMPORTANT] > **Branch Strategy**: I will create a new branch `architecture/editor-in-chief`.
> **Destructive Action**: I will replace `run_graph.py` entirely. The old logic will be preserved in the `gemini` branch history.

## Phase 1: Foundation & State

#### [NEW] [app/state.py](file:///c:/Users/theje/code/anca/app/state.py)

Define the new `ArticleState` schema.

- `Blueprint`: JSON structure with title, audience, and list of `Section` objects.
- `Section`: Heading, description, word count target, search queries.
- `CompletedSections`: List of generated section content.

## Phase 2: Agents (The "Staff")

#### [NEW] [agents/planner.py](file:///c:/Users/theje/code/anca/agents/planner.py)

- **Role**: Editor-in-Chief.
- **Input**: User Topic.
- **Output**: `Blueprint` (JSON).

#### [NEW] [agents/writer.py](file:///c:/Users/theje/code/anca/agents/writer.py)

- **Role**: Section Writer.
- **Input**: Single `Section` object + Blueprint context.
- **Actions**: Focused `retrieve_context` (Research).
- **Output**: Markdown string (~500 words).

#### [NEW] [agents/assembler.py](file:///c:/Users/theje/code/anca/agents/assembler.py)

- **Role**: Final Editor.
- **Input**: All `CompletedSections`.
- **Actions**: `save_article`.
- **Output**: Final Markdown file.

## Phase 3: The Workflow (The "Brain")

#### [MODIFY] [run_graph.py](file:///c:/Users/theje/code/anca/run_graph.py)

Implement the LangGraph **Map-Reduce** flow:

1.  **Planner Node**: Generates the Blueprint.
2.  **Writer Map**: Iterates over `Blueprint.sections` and maps them to `Writer` nodes (using `Send` API in LangGraph).
3.  **Assembler Node**: Reduces the results into one file.

## Execution Steps

1.  **Commit**: Save current `gemini` state.
2.  **Branch**: Create `architecture/editor-in-chief`.
3.  **Scaffold**: Create state and agent files.
4.  **Orchestrate**: Build the new graph in `run_graph.py`.
5.  **Test**: Run with "Benefits of Cold Brew Coffee".
