import os
from typing import List, Optional, Dict, Any

import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
TIMEOUT = 120


def health_check() -> Dict[str, Any]:
    try:
        resp = requests.get(f"{BACKEND_URL}/health", timeout=5)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to backend. Is the server running?"}
    except Exception as e:
        return {"error": str(e)}


def upload_documents(files: List) -> Dict[str, Any]:
    try:
        file_tuples = [
            ("files", (f.name, f.getvalue(), f.type or "application/octet-stream"))
            for f in files
        ]
        resp = requests.post(f"{BACKEND_URL}/documents/upload", files=file_tuples, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        try:
            return {"error": e.response.json().get("detail", str(e))}
        except Exception:
            return {"error": str(e)}
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to backend."}
    except Exception as e:
        return {"error": str(e)}


def list_documents() -> List[Dict[str, Any]]:
    try:
        resp = requests.get(f"{BACKEND_URL}/documents/", timeout=10)
        resp.raise_for_status()
        return resp.json().get("documents", [])
    except Exception:
        return []


def delete_document(doc_id: str) -> Dict[str, Any]:
    try:
        resp = requests.delete(f"{BACKEND_URL}/documents/{doc_id}", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        try:
            return {"error": e.response.json().get("detail", str(e))}
        except Exception:
            return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}


def ask_question(question: str, doc_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    payload = {"question": question}
    if doc_ids:
        payload["doc_ids"] = doc_ids
    try:
        resp = requests.post(f"{BACKEND_URL}/query", json=payload, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        try:
            return {"error": e.response.json().get("detail", str(e))}
        except Exception:
            return {"error": str(e)}
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to backend."}
    except requests.exceptions.Timeout:
        return {"error": "Request timed out. The LLM is still processing — try again."}
    except Exception as e:
        return {"error": str(e)}
