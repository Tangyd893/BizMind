"""RAGAS evaluation service — run benchmark, compute metrics.

Supports baseline and agent modes, reads Golden QA from golden_qa.jsonl.
"""

import json
import time
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import EvalRun, User
from app.rag.llm_client import get_llm_client
from app.rag.retriever import retrieve
from app.schemas.eval import EvalRunResponse


def _load_dataset(name: str = "default") -> list[dict]:
    """Load Golden QA pairs from a JSONL file."""
    settings = get_settings()
    dataset_path = Path(settings.storage_path).parent / "golden_qa.jsonl"
    if name != "default" and Path(name).exists():
        dataset_path = Path(name)
    if not dataset_path.exists():
        return []
    qa_pairs = []
    with open(dataset_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                qa_pairs.append(json.loads(line))
    return qa_pairs


async def _run_baseline_eval(
    qa_pairs: list[dict],
    tenant_id: str,
    progress_callback=None,
) -> dict:
    """Run baseline RAG on each QA pair and compute RAGAS metrics."""
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness

    empty_metrics = {
        "faithfulness": 0.0, "answer_relevancy": 0.0,
        "context_precision": 0.0, "context_recall": 0.0,
    }
    if not qa_pairs:
        return empty_metrics

    questions = []
    answers = []
    contexts_list = []

    for i, qa in enumerate(qa_pairs):
        question = qa["question"]
        _ground_truth = qa.get("expected_answer", qa.get("answer", ""))

        # Retrieve
        result = await retrieve(question, tenant_id)
        context_texts = [c.text_preview for c in result.chunks]

        # Generate answer
        llm = get_llm_client()
        prompt = f"""Answer the question based on the context. Question: {question}
Context:
{chr(10).join(f'- {c}' for c in context_texts)}
"""
        answer = ""
        async for token in llm.chat_stream([{"role": "user", "content": prompt}]):
            answer += token

        questions.append(question)
        answers.append(answer)
        contexts_list.append(context_texts)

        if progress_callback:
            progress_callback(i + 1, len(qa_pairs))

    try:
        dataset = Dataset.from_dict({
            "question": questions,
            "answer": answers,
            "contexts": contexts_list,
        })
        result = evaluate(
            dataset,
            metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        )
        return {
            "faithfulness": float(result.get("faithfulness", 0.0) or 0.0),
            "answer_relevancy": float(result.get("answer_relevancy", 0.0) or 0.0),
            "context_precision": float(result.get("context_precision", 0.0) or 0.0),
            "context_recall": float(result.get("context_recall", 0.0) or 0.0),
        }
    except Exception:
        return empty_metrics


async def run_eval(
    session: AsyncSession,
    admin: User,
    mode: str,
    dataset_name: str = "default",
    sample_limit: int | None = None,
) -> dict:
    """Trigger an eval run (background). Returns run_id for status polling."""
    run_id = uuid.uuid4()

    # Create DB record
    eval_run = EvalRun(
        id=run_id,
        tenant_id=admin.tenant_id,
        triggered_by=admin.id,
        mode=mode,
        dataset_path=dataset_name,
        sample_count=0,
        metrics={},
        config_snapshot={
            "chunk_size": get_settings().chunk_size,
            "top_k": get_settings().retrieval_top_k,
        },
    )
    session.add(eval_run)
    await session.commit()

    # Load dataset
    qa_pairs = _load_dataset(dataset_name)
    if sample_limit and sample_limit < len(qa_pairs):
        qa_pairs = qa_pairs[:sample_limit]

    if not qa_pairs:
        eval_run.metrics = {"error": "No QA pairs found"}
        eval_run.duration_sec = 0
        await session.commit()
        return {"run_id": str(run_id), "status": "completed"}

    eval_run.sample_count = len(qa_pairs)

    # Run evaluation
    start = time.perf_counter()
    if mode == "agent":
        metrics = await _run_agent_eval(qa_pairs, str(admin.tenant_id))
    elif mode == "both":
        baseline = await _run_baseline_eval(qa_pairs, str(admin.tenant_id))
        agent = await _run_agent_eval(qa_pairs, str(admin.tenant_id))
        metrics = {"baseline": baseline, "agent": agent}
    else:
        metrics = await _run_baseline_eval(qa_pairs, str(admin.tenant_id))
    eval_run.metrics = metrics
    eval_run.duration_sec = int(time.perf_counter() - start)
    await session.commit()

    return {"run_id": str(run_id), "status": "completed"}


async def _run_agent_eval(
    qa_pairs: list[dict],
    tenant_id: str,
    progress_callback=None,
) -> dict:
    """Run agentic RAG on each QA pair and compute RAGAS metrics."""
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness

    empty_metrics = {
        "faithfulness": 0.0, "answer_relevancy": 0.0,
        "context_precision": 0.0, "context_recall": 0.0,
    }
    if not qa_pairs:
        return empty_metrics

    questions = []
    answers = []
    contexts_list = []

    for i, qa in enumerate(qa_pairs):
        question = qa["question"]
        _ground_truth = qa.get("expected_answer", qa.get("answer", ""))

        # Use hybrid retriever for agent mode
        from app.rag.retriever import hybrid_retrieve
        result = await hybrid_retrieve(question, tenant_id)
        context_texts = [c.text_preview for c in result.chunks]

        # Generate answer with richer prompt
        llm = get_llm_client()
        context_block = "\n".join(f"- {c}" for c in context_texts)
        prompt = (
            "You are an enterprise assistant. Answer based on the context.\n\n"
            f"Context:\n{context_block}\n\n"
            f"Question: {question}"
        )
        answer = ""
        async for token in llm.chat_stream([{"role": "user", "content": prompt}]):
            answer += token

        questions.append(question)
        answers.append(answer)
        contexts_list.append(context_texts)

        if progress_callback:
            progress_callback(i + 1, len(qa_pairs))

    try:
        dataset = Dataset.from_dict({
            "question": questions,
            "answer": answers,
            "contexts": contexts_list,
        })
        result = evaluate(
            dataset,
            metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        )
        return {
            "faithfulness": float(result.get("faithfulness", 0.0) or 0.0),
            "answer_relevancy": float(result.get("answer_relevancy", 0.0) or 0.0),
            "context_precision": float(result.get("context_precision", 0.0) or 0.0),
            "context_recall": float(result.get("context_recall", 0.0) or 0.0),
        }
    except Exception:
        return empty_metrics


async def list_eval_runs(
    session: AsyncSession,
    tenant_id: str,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[dict], int]:
    """List eval runs for a tenant."""
    count_stmt = select(EvalRun).where(EvalRun.tenant_id == tenant_id)
    total = len((await session.execute(count_stmt)).scalars().all())

    stmt = (
        select(EvalRun)
        .where(EvalRun.tenant_id == tenant_id)
        .order_by(EvalRun.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = (await session.execute(stmt)).scalars().all()

    items = [EvalRunResponse.model_validate(r).model_dump() for r in rows]
    return items, total


async def get_eval_run(
    session: AsyncSession,
    run_id: str,
    tenant_id: str,
) -> dict | None:
    """Get a single eval run."""
    result = await session.execute(
        select(EvalRun).where(EvalRun.id == run_id, EvalRun.tenant_id == tenant_id)
    )
    run = result.scalar_one_or_none()
    if run is None:
        return None
    return EvalRunResponse.model_validate(run).model_dump()
