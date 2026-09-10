"""
AI Job Application Analyzer — Phase 12.

POST /api/job/analyze

Analyzes a resume against a job description using structured prompting.
Returns a JSON result with match_score, matched_skills (with evidence),
missing_skills, and a recommendation.

Key prompt engineering principles applied here:
  - Structured JSON output with explicit schema
  - Grounding rule: every matched skill MUST cite evidence from the resume
  - Hallucination prevention: "If a skill is not in the resume, do not assume"
  - Temperature 0 for deterministic, consistent results
  - Response validated with Pydantic
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.schemas.llm import LLMRequest
from app.services.llm.registry import get_provider
from app.services.evaluation_service import evaluate_json_validity

router = APIRouter()
logger = get_logger(__name__)

# The carefully crafted structured prompt (V3 — see docs/prompt-engineering.md)
_JOB_SYSTEM_PROMPT = """You are an expert technical recruiter and skills assessment specialist.

You MUST follow these rules without exception:
1. ONLY identify skills that are explicitly mentioned or clearly demonstrated in the resume text.
2. NEVER assume, infer, or extrapolate skills not present in the resume.
3. Every matched skill MUST include a direct quote or reference from the resume as evidence.
4. If a required skill is not in the resume, list it as missing — do not guess.
5. Your response must be valid JSON only. No explanations, no markdown, no text outside the JSON.
"""

_JOB_USER_PROMPT = """Analyze this resume against the job description.

JOB DESCRIPTION:
---
{job_description}
---

RESUME:
---
{resume}
---

Return ONLY this JSON structure (no other text):
{{
  "match_score": <integer 0-100>,
  "matched_skills": [
    {{
      "skill": "<skill name>",
      "evidence": "<exact quote or reference from the resume>"
    }}
  ],
  "missing_skills": ["<skill not found in resume>"],
  "strengths": ["<notable strength from resume>"],
  "recommendation": "<one sentence: hire / interview / reject with brief reason>",
  "confidence": <float 0.0-1.0>
}}"""


@router.post(
    "/job/analyze",
    summary="Analyze a resume against a job description",
    description="""
Structured prompt engineering demo: resume vs job description analysis.

**Prompt engineering principles used:**
- Explicit grounding rule (no skill invention)
- Evidence requirement for every match
- Structured JSON output with Pydantic validation
- Temperature 0 for deterministic results
- JSON repair if model returns invalid JSON

**The model CANNOT invent skills.** Every matched skill includes evidence
from the resume text. If a skill is absent, it's listed as missing.
""",
    tags=["Job Analyzer"],
)
async def analyze_job_application(
    request: dict,
    db: AsyncSession = Depends(get_db),
) -> dict:
    resume = (request.get("resume") or "").strip()
    job_description = (request.get("job_description") or "").strip()
    provider = (request.get("provider") or "mock").strip()
    model = request.get("model") or ""

    if not resume:
        raise HTTPException(status_code=422, detail="resume field is required and cannot be empty.")
    if not job_description:
        raise HTTPException(status_code=422, detail="job_description field is required and cannot be empty.")

    user_prompt = _JOB_USER_PROMPT.format(
        job_description=job_description[:4000],
        resume=resume[:4000],
    )

    import time
    start = time.perf_counter()

    try:
        provider_obj = get_provider(provider)
        llm_req = LLMRequest(
            system_prompt=_JOB_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            provider=provider,
            model=model,
            temperature=0.0,   # deterministic for structured output
            max_tokens=1024,
        )
        llm_resp = await provider_obj.generate_structured(llm_req)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"LLM call failed: {type(e).__name__}")

    latency_ms = round((time.perf_counter() - start) * 1000)

    # Validate JSON
    json_eval = evaluate_json_validity(
        llm_resp.content,
        expected_schema={
            "match_score": "integer",
            "matched_skills": "array",
            "missing_skills": "array",
            "recommendation": "string",
        }
    )

    logger.info(
        "job_analysis_complete",
        provider=provider,
        json_valid=llm_resp.json_valid,
        latency_ms=latency_ms,
    )

    return {
        "result": llm_resp.parsed or {},
        "raw_response": llm_resp.content,
        "json_valid": llm_resp.json_valid,
        "json_repair_attempted": llm_resp.json_repair_attempted,
        "json_validation": {
            "score": json_eval.score,
            "passed": json_eval.passed,
            "reason": json_eval.reason,
        },
        "provider": provider,
        "model": llm_resp.model,
        "latency_ms": latency_ms,
        "prompt_notes": {
            "technique": "structured prompting + grounding rules",
            "temperature": 0.0,
            "hallucination_prevention": "explicit rule: every matched skill requires evidence from the resume",
        }
    }
