# Evaluation Methodology

How PromptLab measures prompt quality. Every metric is computed from **actual
test runs** — no fabricated scores.

---

## Core Principle

> Prefer deterministic checks. Use LLM-as-judge only where deterministic methods
> are genuinely insufficient. Always document which method was used.

Every evaluation result records:
```json
{
  "score": 0-100,
  "passed": true/false,
  "reason": "Human-readable explanation",
  "evidence": "Specific text supporting the verdict",
  "evaluation_method": "deterministic | schema_check | semantic | llm_judge"
}
```

---

## Metrics

### 1. Accuracy

**What it measures:** Does the response contain the correct answer?

**Methods (in preference order):**
1. **Exact match** — normalised string comparison (lowercase, strip whitespace)
2. **Contains match** — expected answer appears anywhere in response
3. **Numeric match** — extract and compare numbers with tolerance
4. **Semantic similarity** — cosine similarity of embeddings (threshold ≥ 0.85)

**When LLM judge is used:** Complex long-form answers where none of the above
methods can determine correctness. Explicitly labelled in results.

**Limitation:** Semantic similarity can incorrectly score paraphrases as wrong
(false negative) or near-synonyms as right (false positive).

---

### 2. Relevance

**What it measures:** Does the response address the actual question?

**Method:**
- Extract key terms from the user prompt (noun phrases, key verbs)
- Compute overlap between key terms and response text
- Score = (matched terms / total key terms) × 100

**Limitation:** Keyword overlap doesn't capture all relevance dimensions.
A highly relevant response using different vocabulary can score low.

---

### 3. Tone

**What it measures:** Does the response match the requested tone?

**Method:** Rule-based classifier using curated word lists and patterns:
- Professional/formal: technical vocabulary, no slang, complete sentences
- Friendly/casual: contractions, conversational phrasing
- Concise: response length vs expected length ratio

**Limitation:** Tone is partly subjective. The classifier captures objective
signals but misses nuance.

---

### 4. Consistency

**What it measures:** Does the model give consistent answers when asked the
same question multiple times?

**Method:**
1. Run the same prompt 3× with the same parameters
2. Compute pairwise semantic similarity between the 3 responses
3. Consistency score = mean pairwise similarity × 100

**Important:** This makes 3 real API calls. Each call is recorded as a
separate experiment with the same `test_case_id`.

**Limitation:** Some variation is expected and acceptable. Perfect consistency
(score = 100) at temperature > 0 would actually be suspicious.

---

### 5. JSON Validity

**What it measures:** Does the response parse as valid JSON matching the expected schema?

**Method:** Fully deterministic.
1. Attempt `json.loads()` on the response
2. If parse succeeds, validate against the Pydantic schema
3. Score: 100 (valid + schema match), 50 (valid JSON, schema mismatch), 0 (invalid JSON)

**Repair strategy:** If JSON is invalid, attempt to extract the JSON object using
regex, then retry parsing. The original response and repair attempt are both stored.

---

### 6. Groundedness (RAG only)

**What it measures:** Are the model's claims supported by the retrieved chunks?

**Method:**
1. Extract factual claims from the response (sentence-level)
2. For each claim, search retrieved chunks for supporting text
3. Score = (supported claims / total claims) × 100

**Limitation:** Claim extraction and support matching are approximate.
Paraphrased support is harder to detect than verbatim quotes.

---

### 7. Safety

**What it measures:** Does the response avoid harmful, policy-violating, or
injection-compromised content?

**Method:** Rule-based checks (see `safety_service.py`):
- Prompt injection detection (did the model follow injected instructions?)
- PII pattern detection (emails, phone numbers, SSNs in output)
- Refusal detection (did the model refuse when it should have?)
- Unsafe instruction detection

**Limitation:** Safety evaluation cannot cover all possible harmful outputs.
The rule-based approach catches known patterns; novel attacks may not be detected.

---

## LLM-as-Judge: When and Limitations

LLM-as-judge is used only for:
- Open-ended accuracy on complex long-form answers
- Nuanced relevance where keyword overlap is clearly insufficient

**Known limitations:**
- The judge LLM can hallucinate about quality the same way any LLM can
- Same-provider evaluation may be biased toward that provider's style
- Results are probabilistic — the same judge may score differently on re-runs
- Position bias: the judge may prefer the first answer presented
- Self-enhancement bias: GPT-4 may rate GPT-4 outputs higher

**PromptLab mitigation:**
- All LLM-judge evaluations are explicitly labelled
- Human review is recommended before trusting LLM-judge scores
- We compare LLM-judge scores against deterministic baselines when possible

---

## Evaluation Datasets

See `evaluation/datasets/` for the test case files.

Each test case:
```json
{
  "id": "case_001",
  "input": "What is the capital of France?",
  "expected_output": "Paris",
  "expected_behavior": "Return only the city name",
  "category": "factual_qa",
  "difficulty": "easy"
}
```

Target dataset sizes per category:
- Classification: 20 cases
- Summarisation: 20 cases
- Extraction: 20 cases
- RAG: 20 cases
- Safety: 20 cases

Phase 7 starts with 10 cases per category and expands to 20+ in Phase 13.

---

## Interpreting Results

| Score range | Interpretation |
|---|---|
| 90–100 | Excellent — likely production ready |
| 70–89 | Good — minor improvements possible |
| 50–69 | Fair — significant iteration needed |
| <50 | Poor — prompt needs fundamental rethinking |

**Important:** These thresholds are heuristic guides, not absolute standards.
Domain requirements and risk tolerance determine what "good enough" means.
