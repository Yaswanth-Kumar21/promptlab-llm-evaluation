"""
RAGService — retrieval-augmented generation pipeline.

Pipeline:
  question → embed → search vector store → build context prompt
  → LLM → answer with source citations

Security:
  Retrieved chunks are wrapped in <context> delimiters to prevent
  indirect prompt injection. The system prompt explicitly instructs
  the model to use only text inside these delimiters.
"""

from typing import List, Optional

from app.core.logging import get_logger
from app.schemas.rag import RAGQueryRequest, RAGQueryResponse, RAGSource
from app.services.embedding_service import embed_single
from app.services.llm.registry import get_provider
from app.services.vector_store import get_vector_store, SearchResult
from app.schemas.llm import LLMRequest

logger = get_logger(__name__)

# Minimum similarity score — chunks below this threshold are too weak to include
MIN_SIMILARITY = 0.25

RAG_SYSTEM_PROMPT = """You are a helpful assistant that answers questions based strictly on the provided context.

Rules you MUST follow:
1. Only use information from the text inside <context> tags.
2. If the answer is not in the context, say exactly: "I don't have enough information in the provided context to answer this question."
3. Do not use your training knowledge to fill gaps.
4. After your answer, list the sources you used from the context.
5. Keep your answer concise and accurate.
"""


async def query_rag(
    request: RAGQueryRequest,
    db=None,
) -> RAGQueryResponse:
    """
    Full RAG pipeline:
      1. Embed the question
      2. Retrieve top-k similar chunks
      3. Filter by minimum similarity
      4. Build context-injected prompt with explicit delimiters
      5. Call LLM
      6. Return answer + sources
    """
    # 1. Embed query
    query_embedding = embed_single(request.question)

    # 2. Retrieve
    store = get_vector_store()
    results: List[SearchResult] = store.search(
        query_embedding=query_embedding,
        k=request.top_k,
        document_id=request.document_id,
    )

    # 3. Filter weak results
    filtered = [r for r in results if r.score >= MIN_SIMILARITY]

    if not filtered:
        return RAGQueryResponse(
            question=request.question,
            answer="I don't have enough information in the provided context to answer this question.",
            sources=[],
            chunks_retrieved=0,
            provider=request.provider,
            model="",
            latency_ms=0,
        )

    # 4. Build context prompt with delimiters (injection defence)
    context_parts = []
    sources: List[RAGSource] = []

    for i, result in enumerate(filtered):
        chunk = result.chunk
        meta = chunk.metadata
        source_label = f"[Source {i+1}: {meta.get('filename', 'unknown')}"
        if meta.get("page"):
            source_label += f", page {meta['page']}"
        source_label += f", chunk {chunk.chunk_index}]"

        context_parts.append(f"{source_label}\n{chunk.content}")
        sources.append(RAGSource(
            document_id=chunk.document_id,
            chunk_id=chunk.id,
            filename=meta.get("filename", "unknown"),
            page=meta.get("page"),
            chunk_index=chunk.chunk_index,
            relevance_score=round(result.score, 3),
            content_preview=chunk.content[:200] + "…" if len(chunk.content) > 200 else chunk.content,
        ))

    context_text = "\n\n---\n\n".join(context_parts)

    user_prompt = f"""<context>
{context_text}
</context>

Question: {request.question}

Answer based only on the context above. If the answer is not present, say so."""

    # 5. Call LLM
    import time
    start = time.perf_counter()

    try:
        provider = get_provider(request.provider)
        llm_request = LLMRequest(
            system_prompt=RAG_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            provider=request.provider,
            model=request.model,
            temperature=0.1,   # low temp for factual RAG
            max_tokens=1024,
        )
        llm_response = await provider.generate(llm_request)
        answer = llm_response.content
        model = llm_response.model
        error = llm_response.error_message
    except Exception as e:
        logger.error("rag_llm_failed", error=str(e))
        answer = f"LLM call failed: {type(e).__name__}"
        model = ""
        error = str(e)

    latency_ms = round((time.perf_counter() - start) * 1000)

    logger.info(
        "rag_query_complete",
        chunks=len(filtered),
        provider=request.provider,
        latency_ms=latency_ms,
    )

    return RAGQueryResponse(
        question=request.question,
        answer=answer,
        sources=sources,
        chunks_retrieved=len(filtered),
        provider=request.provider,
        model=model,
        latency_ms=latency_ms,
        error=error,
    )
