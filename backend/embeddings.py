import os
import uuid
from typing import List, Optional, Dict

import chromadb
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

VECTORSTORE_DIR = os.getenv("VECTORSTORE_DIR", os.path.join(os.path.dirname(__file__), "..", "vectorstore"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))
COLLECTION_NAME = "documents"

_model: Optional[SentenceTransformer] = None
_client: Optional[chromadb.PersistentClient] = None
_collection = None
_doc_chunk_registry: Dict[str, int] = {}


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def load_vectorstore() -> None:
    global _client, _collection
    os.makedirs(VECTORSTORE_DIR, exist_ok=True)
    _client = chromadb.PersistentClient(path=VECTORSTORE_DIR)
    _collection = _client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )


def add_documents(documents: List[Document], doc_id: str) -> int:
    global _doc_chunk_registry

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = splitter.split_documents(documents)
    if not chunks or _collection is None:
        return 0

    model = _get_model()
    texts = [c.page_content for c in chunks]
    embeddings = model.encode(texts, normalize_embeddings=True).tolist()

    ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
    metadatas = []
    for c in chunks:
        meta = {k: str(v) for k, v in c.metadata.items()}
        meta["doc_id"] = doc_id
        metadatas.append(meta)

    _collection.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
    _doc_chunk_registry[doc_id] = len(chunks)
    return len(chunks)


def delete_documents(doc_id: str) -> None:
    global _doc_chunk_registry
    if _collection is None or doc_id not in _doc_chunk_registry:
        return
    _collection.delete(where={"doc_id": doc_id})
    del _doc_chunk_registry[doc_id]


def similarity_search(
    query: str,
    k: int = 5,
    filter_doc_ids: Optional[List[str]] = None
) -> List[Document]:
    if _collection is None:
        return []

    model = _get_model()
    query_embedding = model.encode([query], normalize_embeddings=True).tolist()

    where = {"doc_id": {"$in": filter_doc_ids}} if filter_doc_ids else None

    try:
        results = _collection.query(
            query_embeddings=query_embedding,
            n_results=min(k, max(1, _collection.count())),
            where=where,
            include=["documents", "metadatas", "distances"]
        )
    except Exception:
        return []

    docs = []
    for text, meta in zip(results["documents"][0], results["metadatas"][0]):
        docs.append(Document(page_content=text, metadata=meta))
    return docs


def get_chunk_count(doc_id: str) -> int:
    return _doc_chunk_registry.get(doc_id, 0)


def has_documents() -> bool:
    return _collection is not None and _collection.count() > 0


def get_all_doc_ids() -> List[str]:
    return list(_doc_chunk_registry.keys())
