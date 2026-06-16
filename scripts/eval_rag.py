#!/usr/bin/env python3
"""RAGAS benchmark runner — run evaluation from command line.

Usage:
    cd backend
    uv run python ../scripts/eval_rag.py --mode baseline
    uv run python ../scripts/eval_rag.py --mode agent
    uv run python ../scripts/eval_rag.py --mode both
"""

from __future__ import annotations

import argparse
import asyncio
import json
import time

async def _get_demo_tenant_id() -> str:
    """Resolve the demo tenant ID at runtime."""
    from app.db.session import AsyncSessionLocal
    from sqlalchemy import text

    async with AsyncSessionLocal() as s:
        r = await s.execute(text("SELECT id FROM tenants WHERE name = 'Demo Corp' LIMIT 1"))
        row = r.fetchone()
        return str(row[0]) if row else "00000000-0000-0000-0000-000000000001"


async def _main(mode: str = "baseline", sample_limit: int | None = None) -> int:
    from app.rag.retriever import hybrid_retrieve, retrieve
    from app.rag.llm_client import get_llm_client
    from app.config import get_settings

    # Load dataset
    import sys
    from pathlib import Path
    dataset_path = Path(__file__).parent.parent / "data" / "golden_qa.jsonl"
    if not dataset_path.exists():
        print(f"ERROR: Dataset not found at {dataset_path}", file=sys.stderr)
        return 1

    qa_pairs = []
    with open(dataset_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                qa_pairs.append(json.loads(line))

    if sample_limit:
        qa_pairs = qa_pairs[:sample_limit]

    demo_tenant_id = await _get_demo_tenant_id()
    print(f"Running {mode} eval on {len(qa_pairs)} QA pairs (tenant={demo_tenant_id})...")
    start = time.perf_counter()

    questions = []
    answers = []
    contexts_list = []
    ground_truths = []

    for i, qa in enumerate(qa_pairs):
        question = qa["question"]
        ground_truth = qa.get("expected_answer", qa.get("answer", ""))

        # Retrieve
        if mode == "agent":
            result = await hybrid_retrieve(question, demo_tenant_id)
        else:
            result = await retrieve(question, demo_tenant_id)
        context_texts = [c.text_preview for c in result.chunks]

        # Generate
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
        ground_truths.append(ground_truth)

        # Progress
        elapsed = time.perf_counter() - start
        rate = (i + 1) / elapsed if elapsed > 0 else 0
        print(f"  [{i+1}/{len(qa_pairs)}] {question[:60]}... ({rate:.1f} q/s)")

    print(f"Retrieval + generation done in {time.perf_counter() - start:.1f}s")

    # Compute RAGAS
    print("Computing RAGAS metrics...")
    try:
        from ragas import evaluate
        from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
        from ragas.llms import LangchainLLMWrapper
        from langchain_openai import ChatOpenAI, OpenAIEmbeddings
        from datasets import Dataset

        # Configure RAGAS LLM and Embeddings to use the same providers as the app
        cfg = get_settings()
        eval_llm = LangchainLLMWrapper(ChatOpenAI(
            model=cfg.llm_model,
            openai_api_key=cfg.llm_api_key,
            openai_api_base=cfg.llm_base_url,
            temperature=0,
        ))
        eval_embeddings = OpenAIEmbeddings(
            model=cfg.embedding_model,
            openai_api_key=cfg.embedding_api_key or cfg.llm_api_key,
            openai_api_base=cfg.embedding_base_url or cfg.llm_base_url,
        )

        dataset = Dataset.from_dict({
            "question": questions,
            "answer": answers,
            "contexts": contexts_list,
            "reference": ground_truths,
        })
        result = evaluate(
            dataset,
            metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
            llm=eval_llm,
            embeddings=eval_embeddings,
        )

        # Convert EvaluationResult to dict (handle different ragas versions)
        try:
            df = result.to_pandas()
            # Compute mean of each metric column
            metrics = {}
            for key in ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]:
                if key in df.columns:
                    metrics[key] = round(float(df[key].mean()), 4)
                else:
                    metrics[key] = 0.0
        except Exception:
            # Fallback: try dict-like access
            metrics = {}
            for key in ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]:
                try:
                    metrics[key] = round(float(result[key]), 4)
                except (KeyError, TypeError):
                    metrics[key] = 0.0

        print(f"\n=== {mode.upper()} RAGAS Results ===")
        print(json.dumps(metrics, indent=2))

        # Save to file
        out_path = Path(__file__).parent.parent / "docs" / "eval-results.json"
        existing = {}
        if out_path.exists():
            existing = json.loads(out_path.read_text())
        existing[f"{mode}_{int(time.time())}"] = {
            "mode": mode,
            "sample_count": len(qa_pairs),
            "metrics": metrics,
            "duration_sec": int(time.perf_counter() - start),
        }
        out_path.write_text(json.dumps(existing, indent=2))
        print(f"\nResults saved to {out_path}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"RAGAS evaluation failed: {e}")
        return 1

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run RAGAS benchmark")
    parser.add_argument("--mode", choices=["baseline", "agent", "both"], default="baseline")
    parser.add_argument("--sample-limit", type=int, default=None)
    args = parser.parse_args()
    return asyncio.run(_main(args.mode, args.sample_limit))


if __name__ == "__main__":
    raise SystemExit(main())
