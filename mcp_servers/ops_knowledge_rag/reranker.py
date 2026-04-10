"""Cross-Encoder 重排器。"""

from sentence_transformers import CrossEncoder


class CrossEncoderReranker:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self._model = CrossEncoder(model_name)

    def rerank(self, query: str, docs: list[dict], top_k: int = 5) -> list[dict]:
        if not docs:
            return []
        pairs = [(query, d["content"]) for d in docs]
        scores = self._model.predict(pairs)
        for doc, score in zip(docs, scores):
            doc["rerank_score"] = round(float(score), 4)
        docs.sort(key=lambda x: x["rerank_score"], reverse=True)
        return docs[:top_k]
