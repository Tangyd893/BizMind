"""Hybrid retriever — Dense + BM25 + Cross-Encoder Rerank.

P1: single-stage dense retrieval with tenant filter.
P2: hybrid retrieval (dense + BM25) + cross-encoder rerank.
"""

from dataclasses import dataclass, field

from app.config import get_settings
from app.rag.embedder import get_embedding_client
from app.rag.qdrant_store import get_qdrant_store


@dataclass
class RetrievedChunk:
    chunk_id: str
    document_id: str
    source: str
    text_preview: str
    score: float
    page: int | None = None


@dataclass
class RetrievalResult:
    chunks: list[RetrievedChunk] = field(default_factory=list)
    latency_ms: float = 0.0


async def retrieve(
    query: str,
    tenant_id: str,
    top_k: int | None = None,
) -> RetrievalResult:
    """Embed the query and retrieve the top_k most similar chunks for the tenant."""
    import time

    settings = get_settings()
    if top_k is None:
        top_k = settings.retrieval_top_k

    start = time.perf_counter()

    embedder = get_embedding_client()
    store = get_qdrant_store()

    query_vector = await embedder.embed_single(query)
    results = await store.search(
        query_vector=query_vector,
        tenant_id=tenant_id,
        top_k=top_k,
    )

    chunks = [
        RetrievedChunk(
            chunk_id=str(r["chunk_id"]),
            document_id=str(r["document_id"]),
            source=str(r.get("source", "")),
            text_preview=str(r.get("text_preview", "")),
            score=float(r["score"]),
            page=r.get("page"),
        )
        for r in results
    ]

    elapsed = (time.perf_counter() - start) * 1000

    return RetrievalResult(chunks=chunks, latency_ms=elapsed)


async def hybrid_retrieve(
    query: str,
    tenant_id: str,
    top_k: int | None = None,
    rerank_top_k: int | None = None,
) -> RetrievalResult:
    """Hybrid retrieval: Dense + BM25 → fusion → rerank.

    For each chunk, the embedding client must store the full text
    in the text_preview payload field. We use this as the BM25 corpus.
    """
    import time

    from rank_bm25 import BM25Okapi

    settings = get_settings()
    if top_k is None:
        top_k = settings.retrieval_top_k
    if rerank_top_k is None:
        rerank_top_k = getattr(settings, "rerank_top_k", 4)

    # Fetch a larger candidate pool for fusion
    candidate_k = top_k * 2
    start = time.perf_counter()

    embedder = get_embedding_client()
    store = get_qdrant_store()

    # 1. Dense retrieval
    query_vector = await embedder.embed_single(query)
    dense_results = await store.search(
        query_vector=query_vector,
        tenant_id=tenant_id,
        top_k=candidate_k,
    )

    dense_map: dict[str, tuple[float, dict]] = {}
    for r in dense_results:
        cid = str(r["chunk_id"])
        dense_map[cid] = (float(r["score"]), r)

    # 2. BM25 retrieval on the same pool
    all_candidates: list[dict] = []
    corpus_texts: list[str] = []
    for r in dense_results:
        text = str(r.get("text_preview", ""))
        corpus_texts.append(text)
        all_candidates.append(r)

    if corpus_texts:
        tokenized_corpus = [text.lower().split() for text in corpus_texts]
        bm25 = BM25Okapi(tokenized_corpus)
        tokenized_query = query.lower().split()
        bm25_scores = bm25.get_scores(tokenized_query)

        # Normalize BM25 scores to 0-1
        max_bm25 = float(max(bm25_scores)) if len(bm25_scores) > 0 and float(max(bm25_scores)) > 0 else 1.0

        for i, r in enumerate(all_candidates):
            cid = str(r["chunk_id"])
            bm25_norm = float(bm25_scores[i]) / max_bm25 if max_bm25 > 0 else 0.0
            dense_score = dense_map.get(cid, (0.0,))[0]
            # Weighted fusion: 0.7 dense + 0.3 BM25
            fused_score = 0.7 * dense_score + 0.3 * bm25_norm
            dense_map[cid] = (fused_score, r)

    # 3. Sort by fused score and take top candidates for rerank
    sorted_candidates = sorted(dense_map.values(), key=lambda x: x[0], reverse=True)
    rerank_candidates = sorted_candidates[:rerank_top_k * 2]

    # 4. Rerank with Cohere (if key configured)
    final_candidates = rerank_candidates
    cohere_key = getattr(settings, "cohere_api_key", "")
    if cohere_key and len(rerank_candidates) > rerank_top_k:
        try:
            import httpx
            docs = [r[1].get("text_preview", "") for r in rerank_candidates]
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    "https://api.cohere.com/v2/rerank",
                    headers={"Authorization": f"Bearer {cohere_key}"},
                    json={
                        "model": "rerank-english-v3.0",
                        "query": query,
                        "documents": docs,
                        "top_n": rerank_top_k,
                    },
                )
                if resp.status_code == 200:
                    rerank_data = resp.json()
                    rerank_map = {r["index"]: r["relevance_score"] for r in rerank_data["results"]}
                    final_candidates = [
                        (rerank_map.get(i, score), rerank_candidates[i][1])
                        for i, (score, _) in enumerate(rerank_candidates)
                        if i in rerank_map
                    ]
        except Exception:
            pass  # fall through to non-reranked results

    # 5. Build final result
    result_chunks = []
    for score, payload in final_candidates[:top_k]:
        result_chunks.append(RetrievedChunk(
            chunk_id=str(payload["chunk_id"]),
            document_id=str(payload["document_id"]),
            source=str(payload.get("source", "")),
            text_preview=str(payload.get("text_preview", "")),
            score=float(score),
            page=payload.get("page"),
        ))

    elapsed = (time.perf_counter() - start) * 1000
    return RetrievalResult(chunks=result_chunks, latency_ms=elapsed)
