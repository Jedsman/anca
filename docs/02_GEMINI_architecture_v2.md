# Proposal: The "Editor-in-Chief" Hierarchical Architecture

## The Problem
The current architecture (Researcher → Generator) treats "Write a 2000-word article" as a single atomic task. This fails because:
1.  **Context Overload**: The model loses track of early research when writing later sections.
2.  **Laziness**: Models naturally tend to be concise. Fighting this with "write more" prompts is an uphill battle.
3.  **Generic Content**: Examples and data are applied broadly, not specifically to sections.

## The Solution: Hierarchical "Map-Reduce" Pattern
Instead of one agent writing the whole article, we decompose the task into **Planning**, **Section Writing**, and **Assembly**. This effectively turns one hard task into 5-7 easy tasks.

### New Workflow Design

```mermaid
graph TD
    User[User Topic] --> EIC[**Editor-in-Chief**<br>(Planner)]
    
    subgraph "Phase 1: Planning"
        EIC -- "Research Broad Context" --> Research1[Researcher]
        Research1 --> EIC
        EIC --> Outline[**Detailed Outline**<br>Sections, Key Points, Tone]
    end
    
    subgraph "Phase 2: Execution (Map)"
        Outline --> |"Write Section 1"| W1[**Section Writer A**]
        Outline --> |"Write Section 2"| W2[**Section Writer B**]
        Outline --> |"Write Section 3"| W3[**Section Writer C**]
        
        W1 -- "Deep Dive Search" --> R_W1[Research Tool]
        W2 -- "Deep Dive Search" --> R_W2[Research Tool]
        W3 -- "Deep Dive Search" --> R_W3[Research Tool]
    end
    
    subgraph "Phase 3: Assembly (Reduce)"
        W1 & W2 & W3 --> Assembler[**Assembler Agent**<br>Stitches & Smooths Flow]
    end
    
    subgraph "Phase 4: Polish"
        Assembler --> Reviewer[**Reviewer**<br>SEO & Quality Check]
        Reviewer -- "Feedback" --> Assembler
        Reviewer -- "Approved" --> Final[Final Article]
    end
```

### Key Components

#### 1. Editor-in-Chief (The Brain)
*   **Role**: Architect. Does not write prose.
*   **Output**: A structured JSON `ArticleBlueprint` containing:
    *   Title
    *   List of `Section` objects (Heading, Description, Word Count Target, Search Queries).

#### 2. Section Writer (The Specialist)
*   **Role**: Writes ONE specific section (e.g., "The History of Cold Brew").
*   **Input**: The specific `Section` instructions from the Blueprint.
*   **Action**: Performs *focused* research just for this point.
*   **Output**: 400-500 words of high-density content.
*   **Why this works**: It's easy for an LLM to "write 500 words about X". It's hard to "write 2000 words about everything".

#### 3. Assembler (The Compiler)
*   **Role**: Editor.
*   **Action**: Joins sections, fixes transitions (so it doesn't sound like 5 different people wrote it), writes the Introduction and Conclusion (which require knowing the full body content).

## Implementation Strategy (Agentic Pattern)
We can implement this using **LangGraph's Map-Reduce** pattern:
1.  **Node 1 (Planner)**: Generates the list of sections.
2.  **Conditional Edge (Map)**: Spawns a `SectionWriter` node for *each* section in the list (in parallel or sequence).
3.  **Node 3 (Reducer)**: Collects all written sections and produces the final draft.

## Benefits
*   **Unlimited Length**: Want 5000 words? Just plan more sections.
*   **Higher Quality**: Each section gets dedicated research.
*   **Checkpointing**: If Section 3 fails, we retry just Section 3, not the whole article.
