# SEO Auditor Agent

**Model:** `mistral:7b` (strong analysis)  
**Temperature:** 0.3 (consistent critique)

## Purpose
Evaluates content quality and provides actionable feedback for improvement.

## Capabilities
- SEO quality assessment
- E-E-A-T compliance checking
- Readability analysis
- Structured feedback generation

## Evaluation Criteria
1. **SEO**: Keyword usage, heading structure, content length
2. **E-E-A-T**: Experience, Expertise, Authoritativeness, Trustworthiness
3. **Readability**: Clear structure, engaging writing
4. **Completeness**: Topic coverage depth

## Tools
None (analysis only)

## Output
- Quality score (1-10)
- Specific strengths
- Areas for improvement
- Actionable recommendations

## Usage
```python
from agents import create_auditor

auditor = create_auditor(tools=[])
```

## Stage
Introduced in Stage 3 for reflection loop and quality validation.
