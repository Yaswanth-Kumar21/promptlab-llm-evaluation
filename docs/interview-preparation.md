# Interview Preparation

Concise answers to common prompt engineering interview questions,
based **only on features actually implemented in PromptLab**.

---

## Core Concepts

**Q: What is prompt engineering?**
Prompt engineering is the practice of designing, iterating, and evaluating
text instructions that reliably elicit correct, consistent, and safe responses
from an LLM. It treats prompts as testable artefacts — not one-off queries.

**Q: What is zero-shot prompting?**
Asking the model to perform a task using only instructions, with no examples.
It relies entirely on the model's pre-trained knowledge. I use it as a baseline
in PromptLab before testing whether few-shot improves scores.

**Q: What is few-shot prompting?**
Including 2–10 labelled input/output examples in the prompt so the model learns
the expected pattern in-context. In PromptLab, few-shot consistently outperforms
zero-shot on classification and extraction tasks in my evaluation datasets.

**Q: What is structured prompting?**
Designing prompts that force machine-readable output (JSON, YAML) with an explicit
schema. In PromptLab, every structured output is validated with Pydantic. If the
model returns invalid JSON, the failure is recorded and a repair is attempted.

**Q: What is a token?**
The basic unit an LLM processes — roughly 4 characters on average. All API billing
and context limits are in tokens. PromptLab records input and output tokens for
every experiment so you can track cost and context usage over time.

**Q: What is a context window?**
The maximum number of tokens the model can process in one call (input + output combined).
In RAG, retrieved chunks consume tokens, so managing context size is important.
PromptLab's chunking strategy is designed to leave enough room for the answer.

**Q: What does temperature do?**
Scales output randomness. Temperature 0 is deterministic, best for classification
and structured extraction. Temperature 0.7 is balanced. PromptLab records temperature
for every experiment so you can compare its effect on consistency scores.

---

## Evaluation

**Q: How did you evaluate your prompts?**
PromptLab has a multi-metric evaluation engine. Each response is scored on accuracy,
relevance, tone, consistency, JSON validity, groundedness, and safety. I prefer
deterministic methods (exact match, schema validation) and only use LLM-as-judge
for complex open-ended answers where deterministic checks can't work.

**Q: How did you compare prompt versions?**
Each prompt in PromptLab can have multiple versions. I run the same dataset against
V1, V2, V3 and compare scores in a side-by-side chart. The best version is marked.
All experiment results are stored so comparisons are reproducible.

**Q: How did you measure accuracy?**
In preference order: exact match (normalised), contains match, numeric match, then
semantic similarity using cosine distance of embeddings. LLM-as-judge is a last resort
and is always explicitly labelled in the results.

**Q: How did you measure relevance?**
Key term extraction from the user prompt, then overlap scoring with the response.
For RAG, I also check that retrieved chunks are topically relevant to the question.

**Q: How did you test consistency?**
Run the same prompt 3× with identical parameters, then compute pairwise semantic
similarity across the three responses. The mean similarity is the consistency score.
This reveals whether a prompt is stable or produces random-feeling output.

---

## RAG and Embeddings

**Q: What is RAG?**
Retrieval-Augmented Generation. Instead of relying on the model's parametric memory,
you retrieve relevant text from a document store and inject it into the prompt as context.
PromptLab's pipeline: upload → chunk → embed → store in ChromaDB → retrieve → build prompt → answer with citations.

**Q: What are embeddings?**
Dense numerical vectors representing the meaning of text. Similar texts have similar
vectors. PromptLab uses `all-MiniLM-L6-v2` (local, free) to embed document chunks
and query questions. Similarity is measured by cosine distance.

**Q: What is a vector database?**
A database optimised for similarity search on high-dimensional vectors. PromptLab
uses ChromaDB locally. The architecture supports swapping to pgvector or Pinecone
by implementing the `BaseVectorStore` interface.

---

## Safety

**Q: What is prompt injection?**
An attack where malicious text in user input or retrieved documents overrides
the model's instructions. In PromptLab I test both direct injection
("ignore previous instructions") and indirect injection via uploaded documents.

**Q: How did you defend against prompt injection?**
1. Explicit `<context>` delimiters around all retrieved content
2. System prompt instructs the model to use only text inside `<context>`
3. Output validated against Pydantic schema — unexpected fields fail
4. A dedicated attack dataset with 20+ test cases in the Safety Lab

**Q: What is LLM-as-judge?**
Using an LLM to evaluate another LLM's output. Useful for complex open-ended answers
where deterministic methods can't assess quality.

**Q: What are LLM-as-judge limitations?**
The judge can hallucinate about quality. It may be biased toward its own provider's
style. Results are probabilistic — the same judge can score differently on re-runs.
Self-enhancement bias (GPT-4 may prefer GPT-4 outputs). PromptLab explicitly labels
all LLM-judge evaluations and recommends human review for important decisions.

**Q: How did you evaluate bias?**
Controlled pairs: identical prompts where only a non-job-relevant demographic attribute
changes. I compare recommendations and compute a difference score. Results include the
disclaimer that this is experimental and not a comprehensive fairness audit.

---

## Architecture and Engineering

**Q: Why use structured JSON output?**
It makes responses machine-readable, validatable with Pydantic, and downstream-automatable.
It also makes hallucination detection easier — a missing `evidence` field is an explicit
failure rather than a subtle omission in prose.

**Q: How did you handle invalid model output?**
1. Attempt `json.loads()` — if it fails, record the failure with the raw response
2. Try extracting JSON with a regex fallback
3. Validate against the Pydantic schema
4. Store both original and repaired responses
5. Dashboard shows JSON validity rate across all experiments

**Q: Why support multiple LLM providers?**
Different providers have different strengths, prices, and rate limits. The `BaseLLMProvider`
abstraction means I can switch providers by changing one environment variable. It also lets
me compare models objectively — run the same prompt on GPT-4o vs Gemini vs Mistral and
measure which actually scores better on my evaluation dataset.

**Q: What happens if an API fails?**
The provider returns a structured error. The experiment is recorded with `passed=False`
and an `error` field. The UI shows a clear error state (not a blank screen or 500).
Other providers remain available. The mock provider always works as a fallback.

**Q: What would you improve?**
Replace ChromaDB with pgvector for unified storage. Add a human feedback loop (thumbs
up/down) to label evaluation results. Add OpenTelemetry tracing to track every LLM call.
Build a CI/CD pipeline that runs evaluation automatically on every prompt change.

---

*All answers above describe features actually built in PromptLab. No fabricated results.*
