"""文档索引构建器：读取运维文档，分块后写入 Chroma。"""

import os
from pathlib import Path

import chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter


def build_index(
    docs_dir: str = "./data/ops_docs",
    persist_dir: str | None = None,
    chunk_size: int = 512,
    chunk_overlap: int = 64,
):
    persist_dir = persist_dir or os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db")
    client = chromadb.PersistentClient(path=persist_dir)
    collection = client.get_or_create_collection("ops_knowledge")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n## ", "\n### ", "\n\n", "\n", "。", ".", " "],
    )

    docs_path = Path(docs_dir)
    if not docs_path.exists():
        print(f"⚠️  目录不存在: {docs_dir}")
        return

    total = 0
    for fp in docs_path.rglob("*.md"):
        text = fp.read_text(encoding="utf-8")
        chunks = splitter.split_text(text)
        for i, chunk in enumerate(chunks):
            doc_id = f"{fp.stem}_{i}"
            collection.upsert(
                ids=[doc_id],
                documents=[chunk],
                metadatas=[{
                    "source": fp.name,
                    "type": _infer_type(fp.name),
                    "chunk_index": i,
                }],
            )
        total += len(chunks)
        print(f"  ✅ {fp.name}: {len(chunks)} chunks")

    print(f"\n📦 索引构建完成，共 {total} 个分块，存储于 {persist_dir}")


def _infer_type(filename: str) -> str:
    name = filename.lower()
    if "k8s" in name or "kube" in name:
        return "k8s"
    elif "linux" in name or "os" in name:
        return "linux"
    elif "db" in name or "mysql" in name or "redis" in name or "postgres" in name:
        return "database"
    elif "network" in name or "dns" in name or "nginx" in name:
        return "network"
    return "general"


if __name__ == "__main__":
    build_index()
