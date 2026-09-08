# LLM Fundamentals

Reference document for concepts used throughout PromptLab.

---

## Tokens

An LLM does not process text as characters or words. It uses a **tokeniser**
to split text into subword units called tokens.

- GPT-4 tokeniser: ~4 characters ≈ 1 token on average
- "Hello world" → 2 tokens
- "supercalifragilistic" → ~6 tokens
- Numbers and punctuation can each cost a token

**Why it matters in PromptLab:**
- API costs are billed per token (input + output)
- Context window limits are in tokens
- Token count is recorded in every experiment

---

## Context Window

The maximum number of tokens the model processes in one call.
Input tokens + output tokens must fit within this limit.

| Model | Context window |
|---|---|
| GPT-3.5-turbo | 16,384 |
| GPT-4o-mini | 128,000 |
| GPT-4o | 128,000 |
| Claude 3 Haiku | 200,000 |
| Gemini 1.5 Flash | 1,000,000 |

**RAG implication:** If you retrieve 10 chunks × 500 tokens = 5,000 tokens
consumed by context before the question or answer.

**Common mistake:** Assuming the model uses the full context equally.
Research shows performance degrades for content in the middle of very long
contexts ("lost in the middle" problem).

---

## Temperature

Scales the probability distribution over the model's next-token predictions.

| Value | Behaviour | Best for |
|---|---|---|
| 0.0 | Deterministic (always highest probability) | Classification, extraction, JSON output |
| 0.3 | Low variance, mostly consistent | Summarisation, factual QA |
| 0.7 | Balanced (GPT default) | General purpose |
| 1.0 | Creative, varied | Brainstorming, creative writing |
| >1.0 | Very random | Rarely useful |

**PromptLab records temperature for every experiment** so you can compare
the effect of temperature changes on consistency scores.

---

## Top-p (Nucleus Sampling)

An alternative (or complement) to temperature. Only tokens whose cumulative
probability reaches `top_p` are considered.

- `top_p=1.0` → consider all tokens (default)
- `top_p=0.9` → only top 90% of probability mass
- Used less commonly than temperature in practice

---

## Hallucination

An LLM confidently stating something false or unsupported by context.

**Types:**
1. **Factual** — wrong facts from parametric memory
2. **Contextual** — claims not supported by the provided document
3. **Source fabrication** — invented citations, DOIs, URLs

**Root cause:** LLMs are trained to produce fluent text, not verified facts.
They predict likely tokens — plausible and true are not the same thing.

**Mitigations used in PromptLab:**
- RAG grounds answers in real documents
- Explicit instruction: "Only answer from the provided context"
- Structured output with evidence fields
- Hallucination test dataset with known-false-premise questions
- Automated detection (imperfect — documented in Safety Lab)

---

## System Prompt vs User Prompt

| Role | Purpose |
|---|---|
| System | Persistent instructions that shape all model behaviour: persona, constraints, output format, safety rules |
| User | The current query or task |
| Assistant | The model's response (can be pre-filled for few-shot) |

**PromptLab stores both separately** in `PromptVersion` so you can iterate
on system and user prompts independently.

---

## Sampling Parameters Reference

| Parameter | Range | Effect |
|---|---|---|
| temperature | 0.0 – 2.0 | Randomness |
| top_p | 0.0 – 1.0 | Vocabulary breadth |
| max_tokens | 1 – model limit | Output length cap |
| frequency_penalty | -2.0 – 2.0 | Penalise repeated tokens |
| presence_penalty | -2.0 – 2.0 | Encourage new topics |
| seed | integer | Reproducibility (OpenAI) |

---

## Chain-of-Thought (CoT)

A technique where the model is asked to show its reasoning step-by-step before
answering. Improves accuracy on multi-step reasoning tasks.

**PromptLab approach:** Rather than requesting hidden chain-of-thought, we use
safe alternatives:
- A `reason` field in structured JSON output
- An `evidence` field linking claims to source text
- A `confidence` field with the model's self-assessed certainty

This gives us the benefits of structured reasoning without depending on
implementation-specific thinking tokens.

---

## Prompt Engineering vs Fine-tuning

| Approach | Prompt Engineering | Fine-tuning |
|---|---|---|
| Cost | Only token costs | GPU training cost |
| Speed to iterate | Minutes | Hours/days |
| Data needed | 0–100 examples | 100–10,000+ |
| Model update | None | New model checkpoint |
| Best for | Most tasks | Domain-specific vocabulary, style |

PromptLab focuses on **prompt engineering** — the fastest, cheapest first step
before considering fine-tuning.
