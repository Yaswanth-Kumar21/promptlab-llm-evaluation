# Prompt Engineering: A Practical Walkthrough

This document shows how PromptLab was used to iteratively improve a real prompt.
It is the kind of practical demonstration that answers the interview question:
"Can you walk me through how you improved a prompt?"

---

## Task: Summarise a Technical Article

The goal: summarise a technical article into concise, accurate bullet points.

---

## Version 1 — Baseline (Zero-Shot, Minimal)

```
Summarise this.

[article text]
```

**Problems observed:**
- Output length was unpredictable (1 sentence to 10 paragraphs)
- Occasionally introduced information not in the source ("hallucinated" context)
- Tone varied — sometimes formal, sometimes casual
- No consistent format

**Evaluation scores (actual test run — Phase 7 results):**
*(To be filled after Phase 7 is implemented)*

---

## Version 2 — Format Constraint Added

```
Summarise this in five bullet points.

[article text]
```

**Changes made:** Added an explicit count constraint.

**What improved:**
- Output length became predictable
- Formatting became consistent

**Remaining problems:**
- Bullets were sometimes too long (30+ words)
- Still occasionally added external information
- No vocabulary guidance → some summaries were too technical for a general audience

---

## Version 3 — Role + Constraints + Quality Rules

```
You are a technical writer preparing content for a general audience.

Summarise the following article into exactly five bullet points.

Rules:
- Each bullet must contain fewer than 25 words
- Use only information present in the article — do not add external knowledge
- Use simple English suitable for a non-expert reader
- Start each bullet with a strong action verb

Article:
---
[article text]
---
```

**Changes made:**
1. Added a role persona (technical writer for general audience)
2. Explicit word limit per bullet (< 25 words)
3. Explicit grounding rule (only use article content)
4. Explicit vocabulary rule (simple English)
5. Format rule (start with action verb)

**What improved:**
- Bullet length dropped to consistent 15–22 words
- Hallucination rate reduced significantly
- Vocabulary became more accessible
- Evaluation consistency score improved

**What didn't change:**
- Some articles still produced 4 bullets + 1 very long bullet
  → Fixed in V4 by adding "If a point cannot fit in 25 words, split it into two separate bullets."

---

## Key Lessons

1. **Start minimal, measure first.** V1 gives you a baseline to beat. Don't skip it.
2. **One change at a time.** If you change three things at once, you can't tell which helped.
3. **Measure the change.** Without evaluation scores, "V3 is better" is an opinion.
4. **Constraints reduce variance.** More specific rules = more predictable outputs.
5. **Role prompting shapes vocabulary.** The "technical writer for general audience"
   persona reliably produced simpler language without sacrificing accuracy.
6. **Grounding rules reduce hallucination.** Explicitly forbidding external information
   is more effective than hoping the model stays on-topic.

---

## Prompt Technique Reference

| Technique | When to use | Trade-off |
|---|---|---|
| Zero-shot | Baseline, simple tasks, fast prototyping | Lower accuracy on complex tasks |
| Few-shot | Format-sensitive tasks, niche domains | Costs more tokens |
| Role prompting | Tone/vocabulary control | Needs tuning per domain |
| Structured output | Machine-readable results, validation | LLM must be capable of reliable JSON |
| Constraint-based | Predictable format, reduced hallucination | Can be over-constrained |
| Chain-of-thought | Multi-step reasoning | More tokens, slower |

---

## Anti-Patterns to Avoid

- **Vague instructions:** "Be helpful" → the model decides what helpful means.
- **No output format:** Leads to unpredictable length and structure.
- **Asking for hidden reasoning:** Requesting chain-of-thought tokens the model
  doesn't actually expose is unreliable. Use structured `reason` fields instead.
- **Trusting one run:** A single output tells you nothing about consistency.
  Always evaluate across multiple test cases.
- **Skipping the baseline:** Without V1 scores, you can't prove V3 is better.
