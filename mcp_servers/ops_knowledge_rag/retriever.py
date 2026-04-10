"""混合检索器：向量检索 + BM25 关键词检索 + Cross-Encoder 重排。"""

import os
from pathlib import Path

import chromadb
from rank_bm25 import BM25Okapi

from .reranker import CrossEncoderReranker


class HybridRetriever:
    def __init__(self, persist_dir: str | None = None):
        persist_dir = persist_dir or os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db")
        self._client = chromadb.PersistentClient(path=persist_dir)
        self._collection = self._client.get_or_create_collection("ops_knowledge")
        self._reranker = CrossEncoderReranker()
        self._bm25: BM25Okapi | None = None
        self._bm25_docs: list[dict] = []
        self._build_bm25_index()

    def _build_bm25_index(self):
        """从 Chroma 加载所有文档，构建 BM25 索引。"""
        all_docs = self._collection.get(include=["documents", "metadatas"])
        if not all_docs["documents"]:
            return
        tokenized = [doc.split() for doc in all_docs["documents"]]
        self._bm25 = BM25Okapi(tokenized)
        self._bm25_docs = [
            {"content": doc, "metadata": meta}
            for doc, meta in zip(all_docs["documents"], all_docs["metadatas"])
        ]

    def search(
        self, query: str, top_k: int = 5, filter_type: str | None = None
    ) -> list[dict]:
        fetch_k = max(top_k * 4, 20)

        # 1. 向量检索
        vector_results = self._vector_search(query, fetch_k, filter_type)

        # 2. BM25 检索
        bm25_results = self._bm25_search(query, fetch_k)

        # 3. 合并去重
        merged = self._merge(vector_results, bm25_results)

        # 4. 重排
        if len(merged) > top_k:
            merged = self._reranker.rerank(query, merged, top_k=top_k)

        return merged[:top_k]

    def _vector_search(
        self, query: str, k: int, filter_type: str | None
    ) -> list[dict]:
        where = {"type": filter_type} if filter_type else None
        try:
            results = self._collection.query(
                query_texts=[query], n_results=k, where=where,
                include=["documents", "metadatas", "distances"],
            )
        except Exception:
            return []

        items = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            items.append({
                "content": doc,
                "source": meta.get("source", "unknown"),
                "score": round(1 - dist, 4),
                "method": "vector",
            })
        return items

    def _bm25_search(self, query: str, k: int) -> list[dict]:
        if self._bm25 is None:
            return []
        tokens = query.split()
        scores = self._bm25.get_scores(tokens)
        top_indices = scores.argsort()[-k:][::-1]

        items = []
        for idx in top_indices:
            if scores[idx] <= 0:
                continue
            doc = self._bm25_docs[idx]
            items.append({
                "content": doc["content"],
                "source": doc["metadata"].get("source", "unknown"),
                "score": round(float(scores[idx]), 4),
                "method": "bm25",
            })
        return items

    def _merge(self, a: list[dict], b: list[dict]) -> list[dict]:
        """合并两路结果，按 content 去重。"""
        seen = set()
        merged = []
        for item in a + b:
            key = item["content"][:200]
            if key not in seen:
                seen.add(key)
                merged.append(item)
        return merged

    def get_stats(self) -> dict:
        return {
            "total_chunks": self._collection.count(),
            "bm25_docs": len(self._bm25_docs),
        }
