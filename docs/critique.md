Instead of having the Content Generator judge its own work, we introduce a Quality Assurance (QA) Critic agent and a conditional loop.

1. Define the Graph States

Your graph state needs to track the article content, the target length, and a critique counter.
State Key Purpose Example Value
article_content The full Markdown text drafted by the Generator. # Title...
target_length The minimum required word count (e.g., 1800). 1800
critique_count Tracks how many times the article has been sent back for revision. 0, 1, 2... 2. Introduce Three New Nodes
A. Node: critique_article (The QA Agent)

    Role: A dedicated LLM agent that acts as a critic.

    Function: Accepts the article content and the target length.

    Output: Returns a structured object:

        status: "PASS" or "FAIL"

        feedback: Detailed instructions on which sections need expansion and why (e.g., "Section 4 is too short. Expand the technical details on Step 3 by 200 words").

        word_count: The actual calculated word count (done by a tool, see below).

B. Node: reviser_agent (The Content Generator)

    Role: The original writing agent.

    Function: When it receives a feedback message, it performs the specific expansion/revision tasks requested.

C. Tool: calculate_word_count (The Oracle)

    Role: The utility/tool that uses the accurate Python logic converting Markdown to plain text.

    Function: This tool is called before the critique_article node. It processes article_content and returns the true word count.

3. The Conditional Edge Logic

The flow now becomes deterministic and loop-controlled:
Transition Name Source Node Logic (should_continue function) Destination Node
Complete critique_article If status == "PASS" END
Needs Revision critique_article If status == "FAIL" AND critique_count < 3 reviser_agent
Max Retries critique_article If status == "FAIL" AND critique_count >= 3 END (or HUMAN_REVIEW node)
Why this is Agentically Superior

    Objective Measurement: The word count is measured by a tool (calculate_word_count), which is always accurate, not by the LLM's unreliable internal estimation.

    Clear Exit Logic: The agent knows exactly when to stop: when the critique_article node returns "PASS."

    Controlled Loop: The critique_count state variable prevents the loop from running indefinitely. After 3 (or N) revisions, the graph terminates, preventing cost overruns.

    Actionable Feedback: The Reviser Agent receives explicit instructions on what to fix, rather than being told, "You failed; try again."

This structure uses the graph to enforce external business logic (the word count) rather than trusting an LLM to follow a complex set of internal constraints.
