
import ollama
from app.core.config import settings, chromadb_client
from typing import Sequence
from chromadb.errors import ChromaError


collection = chromadb_client.get_or_create_collection(name="requirements")


def chromadb_healthcheck(client: chromadb_client) -> None:
    try:
        if hasattr(client, "heartbeat"):
            client.heartbeat()
        else:
            client.list_collections()
    except Exception as exc:
        raise ChromaError("ChromaDB healthcheck failed") from exc


def embed_text(text: str) -> Sequence[float]:
    response = ollama.embeddings(
        model=str(settings.EMBED_MODEL),
        prompt=text,
        options=None,
        keep_alive=None
    )
    return response.embedding


def upsert_requirements(doc_id: str, text: str, metadata: dict | None = None):
    vector: Sequence[float] = embed_text(text)

    collection.upsert(
        ids=[doc_id],
        embeddings=[vector],
        metadatas=[metadata or {}],
        documents=[text],
        images=[],
        uris=None
    )


def vector_search(query: str, limit: int = 5):
    vector = embed_text(query)

    results = collection.query(
        query_embeddings=[vector],
        query_texts=None,
        query_images=None,
        query_uris=None,
        ids=None,
        n_results=limit,
        where=None,
        where_document=None,
        include=["metadatas", "documents", "distances"]
    )

    return results
