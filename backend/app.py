import os
import sys
import uuid
from datetime import datetime
from typing import List, Optional
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(__file__))

from loaders import load_document
from embeddings import add_documents, delete_documents, load_vectorstore, has_documents
from rag import answer_question

UPLOAD_DIR = os.getenv("UPLOAD_DIR", os.path.join(os.path.dirname(__file__), "..", "documents"))
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "20"))
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}

_documents: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    load_vectorstore()
    yield


app = FastAPI(
    title="DocuMind AI API",
    description="DocuMind AI — Intelligent Document Q&A System Engine",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    question: str
    doc_ids: Optional[List[str]] = None


class SourceItem(BaseModel):
    filename: str
    page: Optional[str] = None
    preview: str
    doc_id: str


class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceItem]
    model: str


def _ingest_document(file_path: str, doc_id: str) -> None:
    _documents[doc_id]["status"] = "processing"
    try:
        docs = load_document(file_path)
        chunk_count = add_documents(docs, doc_id)
        _documents[doc_id]["status"] = "ready"
        _documents[doc_id]["chunk_count"] = chunk_count
    except Exception as e:
        _documents[doc_id]["status"] = "error"
        _documents[doc_id]["error"] = str(e)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "documents_count": len(_documents),
        "has_embeddings": has_documents(),
    }


@app.post("/documents/upload")
async def upload_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    uploaded = []
    for file in files:
        original_name = file.filename or "unknown"
        ext = os.path.splitext(original_name)[1].lower()

        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported type '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )

        content = await file.read()
        if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(status_code=400, detail=f"'{original_name}' exceeds {MAX_FILE_SIZE_MB}MB.")
        if len(content) == 0:
            raise HTTPException(status_code=400, detail=f"'{original_name}' is empty.")

        doc_id = str(uuid.uuid4())
        save_path = os.path.join(UPLOAD_DIR, f"{doc_id}{ext}")
        with open(save_path, "wb") as f:
            f.write(content)

        _documents[doc_id] = {
            "doc_id": doc_id,
            "filename": original_name,
            "file_path": save_path,
            "status": "pending",
            "chunk_count": 0,
            "uploaded_at": datetime.utcnow().isoformat() + "Z",
            "size_bytes": len(content),
            "error": None,
        }

        background_tasks.add_task(_ingest_document, save_path, doc_id)
        uploaded.append({"doc_id": doc_id, "filename": original_name, "status": "pending"})

    return {"uploaded": uploaded, "count": len(uploaded)}


@app.get("/documents/")
def list_documents():
    docs = [{k: v for k, v in doc.items() if k != "file_path"} for doc in _documents.values()]
    docs.sort(key=lambda d: d.get("uploaded_at", ""), reverse=True)
    return {"documents": docs, "count": len(docs)}


@app.delete("/documents/{doc_id}")
def delete_document(doc_id: str):
    if doc_id not in _documents:
        raise HTTPException(status_code=404, detail="Document not found.")
    doc = _documents[doc_id]
    if os.path.exists(doc.get("file_path", "")):
        os.remove(doc["file_path"])
    delete_documents(doc_id)
    del _documents[doc_id]
    return {"message": f"'{doc['filename']}' deleted.", "doc_id": doc_id}


@app.post("/query", response_model=QueryResponse)
def query_documents(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    if not has_documents():
        raise HTTPException(status_code=400, detail="No documents processed yet. Upload documents first.")
    if request.doc_ids:
        invalid = [d for d in request.doc_ids if d not in _documents]
        if invalid:
            raise HTTPException(status_code=400, detail=f"Unknown doc_ids: {invalid}")
    return answer_question(question=request.question, doc_ids=request.doc_ids)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
