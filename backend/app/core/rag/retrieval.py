from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from langchain_openai import OpenAIEmbeddings

from app.config import settings

COLLECTION = settings.qdrant_collection


def _get_embeddings():
    return OpenAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.openai_api_key,
        dimensions=settings.embedding_dim,
    )


def _get_qdrant() -> QdrantClient:
    if settings.use_local_qdrant:
        return QdrantClient(path=settings.qdrant_local_path)
    return QdrantClient(url=settings.qdrant_url)


async def search_documents(
    query: str,
    top_k: int = 5,
    doc_type: str | None = None,
) -> list[dict]:
    embeddings = _get_embeddings()
    client = _get_qdrant()

    query_vector = embeddings.embed_query(query)

    query_filter = None
    if doc_type:
        query_filter = Filter(
            must=[FieldCondition(key="doc_type", match=MatchValue(value=doc_type))]
        )

    results = client.search(
        collection_name=COLLECTION,
        query_vector=query_vector,
        limit=top_k,
        query_filter=query_filter,
    )

    return [
        {
            "score": r.score,
            "content": r.payload.get("content", ""),
            "filename": r.payload.get("filename", ""),
            "doc_id": r.payload.get("doc_id", ""),
            "chunk_index": r.payload.get("chunk_index", 0),
        }
        for r in results
    ]


async def build_context(query: str, top_k: int = 5) -> str:
    results = await search_documents(query, top_k)
    if not results:
        return ""

    parts = ["以下是相关文档内容：\n"]
    for r in results:
        parts.append(f"--- {r['filename']} (chunk {r['chunk_index']}) ---")
        parts.append(r["content"])
        parts.append("")
    return "\n".join(parts)
