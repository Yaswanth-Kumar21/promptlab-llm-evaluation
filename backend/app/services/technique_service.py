"""
TechniqueService — runs prompt technique demonstrations.

Each technique (zero-shot, few-shot, role, structured, constraint) has a
carefully crafted prompt that demonstrates the concept clearly.

The service uses a real LLM call (or mock) so the user sees actual
model output — not hardcoded fake results.

These prompts are the core of Core Feature 2 (Prompt Techniques).
They are also living examples of prompt engineering best practices.
"""

from app.core.logging import get_logger
from app.schemas.llm import RunPromptRequest, RunPromptResponse, TechniqueRunRequest
from app.services.prompt_service import PromptService
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)

# ── Technique prompt templates ─────────────────────────────────────────────────
# Each entry: (system_prompt, user_prompt_template)
# {user_input} is replaced with the user's actual input at runtime.

TECHNIQUE_PROMPTS: dict[str, tuple[str, str]] = {

    "zero_shot": (
        # System prompt
        "You are a helpful, accurate assistant.",
        # User prompt — no examples, just instruction + input
        "Classify the sentiment of the following text as exactly one of: "
        "positive, negative, or neutral.\n\n"
        "Text: {user_input}\n\n"
        "Reply with just the one-word classification.",
    ),

    "few_shot": (
        # System prompt
        "You are a sentiment classifier. Always reply with exactly one word: "
        "positive, negative, or neutral.",
        # User prompt — 3 labelled examples then the actual input
        """Classify the sentiment. Reply with one word only.

Examples:
Text: "The product is absolutely amazing, shipping was fast!" → positive
Text: "Broken on arrival. Terrible quality. Never buying again." → negative
Text: "It arrived. It works. Nothing special." → neutral

Now classify this:
Text: "{user_input}" → """,
    ),

    "role": (
        # System prompt — persona + expertise
        "You are an expert technical educator with 15 years of experience "
        "explaining complex software concepts to beginners. "
        "You use clear analogies, short sentences, and real-world examples. "
        "You never use jargon without immediately explaining it.",
        # User prompt
        "Explain the following concept to a complete beginner in under 150 words. "
        "Start with a one-sentence plain-English definition, "
        "then give a real-world analogy, "
        "then explain one practical application.\n\n"
        "Concept: {user_input}",
    ),

    "structured": (
        # System prompt — demands JSON
        "You are a data extraction assistant. "
        "You ALWAYS respond with valid JSON only. "
        "No explanations, no markdown, no text outside the JSON object.",
        # User prompt — explicit schema with types
        """Extract the following information from the text and return it as JSON.

Required JSON schema:
{{
  "main_topic": "string — the primary subject",
  "sentiment": "positive | negative | neutral",
  "key_points": ["array of strings, max 3"],
  "confidence": "number between 0.0 and 1.0"
}}

Text to analyse:
{user_input}""",
    ),

    "constraint": (
        # System prompt — precise role
        "You are a technical writer specialising in accessible documentation "
        "for non-expert audiences.",
        # User prompt — layered explicit constraints
        """Summarise the following text. You MUST follow ALL rules:

Rules:
1. Write exactly 3 bullet points — no more, no fewer.
2. Each bullet must be fewer than 20 words.
3. Use only information present in the text — do not add outside knowledge.
4. Use simple English (aim for 8th-grade reading level).
5. Start each bullet with a strong action verb.
6. Do not use the words "text", "article", or "document".

Text:
{user_input}""",
    ),
}


class TechniqueService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def run_technique(self, request: TechniqueRunRequest) -> RunPromptResponse:
        """
        Build the technique-specific prompt and run it.

        Returns the same RunPromptResponse as the regular Playground so the
        frontend can reuse the same result display component.
        """
        technique = request.technique.lower().strip()

        if technique not in TECHNIQUE_PROMPTS:
            available = ", ".join(sorted(TECHNIQUE_PROMPTS.keys()))
            from fastapi import HTTPException
            raise HTTPException(
                status_code=422,
                detail=f"Unknown technique '{technique}'. Available: {available}",
            )

        system_template, user_template = TECHNIQUE_PROMPTS[technique]

        # Inject the user's actual input into the template
        system_prompt = system_template
        user_prompt = user_template.replace("{user_input}", request.user_input)

        run_request = RunPromptRequest(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            provider=request.provider,
            model=request.model,
            temperature=request.temperature,
            max_tokens=512,
            dataset_name=f"technique_demo_{technique}",
        )

        logger.info(
            "technique_run",
            technique=technique,
            provider=request.provider,
            input_length=len(request.user_input),
        )

        service = PromptService(self.db)
        response = await service.run_prompt(run_request)
        return response
