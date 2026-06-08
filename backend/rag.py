import os
from typing import List, Optional, Dict, Any

from groq import Groq
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from embeddings import similarity_search

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
TOP_K_CHUNKS = int(os.getenv("TOP_K_CHUNKS", "5"))

PROMPT_TEMPLATE = """You are an intelligent document assistant. Answer the question using ONLY the context provided below.
If the answer is not present in the context, say "I don't have enough information in the uploaded documents to answer this question."
Be concise, accurate, and do not make up information.

CONTEXT:
{context}

QUESTION:
{question}

ANSWER:"""


def _build_context(docs: List[Document]) -> str:
    parts = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "Unknown")
        page = doc.metadata.get("page", "")
        page_label = f" (Page {page})" if page else ""
        parts.append(f"[Excerpt {i} — {source}{page_label}]\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


def _build_sources(docs: List[Document]) -> List[Dict[str, Any]]:
    seen = set()
    sources = []
    for doc in docs:
        source = doc.metadata.get("source", "Unknown")
        page = doc.metadata.get("page", "")
        key = (source, page)
        if key not in seen:
            seen.add(key)
            preview = doc.page_content
            if len(preview) > 250:
                preview = preview[:250].rsplit(" ", 1)[0] + "..."
            sources.append({
                "filename": source,
                "page": page,
                "preview": preview,
                "doc_id": doc.metadata.get("doc_id", "")
            })
    return sources


def answer_question(
    question: str,
    doc_ids: Optional[List[str]] = None,
    k: int = TOP_K_CHUNKS
) -> Dict[str, Any]:
    relevant_docs = similarity_search(query=question, k=k, filter_doc_ids=doc_ids)

    if not relevant_docs:
        return {
            "answer": "No relevant content found. Please upload and process documents first.",
            "sources": [],
            "model": GROQ_MODEL
        }

    context = _build_context(relevant_docs)
    prompt = PROMPT_TEMPLATE.format(context=context, question=question)

    if not GROQ_API_KEY:
        return {
            "answer": "Groq API key not set. Add GROQ_API_KEY to your .env file. Get a free key at https://console.groq.com/",
            "sources": _build_sources(relevant_docs),
            "model": GROQ_MODEL
        }

    try:
        client = Groq(api_key=GROQ_API_KEY)
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=GROQ_MODEL,
            temperature=0.1,
            max_tokens=512,
        )
        answer = chat_completion.choices[0].message.content.strip()
    except Exception as e:
        error = str(e).lower()
        if "api_key" in error or "authentication" in error or "401" in error:
            answer = "Invalid Groq API key. Please check your GROQ_API_KEY in the .env file."
        elif "rate" in error or "429" in error:
            answer = "Groq API rate limit reached. Please wait a moment and try again."
        elif "connection" in error or "network" in error:
            answer = "Cannot connect to Groq API. Please check your internet connection."
        else:
            answer = f"LLM error: {str(e)}"

    return {
        "answer": answer,
        "sources": _build_sources(relevant_docs),
        "model": GROQ_MODEL
    }
