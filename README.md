# 🧠 DocuMind AI — Intelligent Document Q&A System

> Upload documents. Ask questions. Get accurate, cited answers — powered by Groq cloud LLMs.

---

## ✨ Features

- 📂 **Multi-format Upload** — PDF, DOCX, TXT (up to 20MB each)
- 🔍 **Semantic Search** — ChromaDB vector search with Sentence Transformers
- 🤖 **Groq LLM** — Ultra-fast inference powered by Groq (Llama-3.3-70b-versatile)
- 📎 **Source Citations** — Every answer shows the exact document + page it came from
- 🗂️ **Multi-document** — Query across all documents or filter to specific ones
- ⚡ **Async Ingestion** — Background processing; upload returns instantly

---

## 🏗️ Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│              STREAMLIT FRONTEND (:8501)                  │
│   Chat Page (main.py)  │  Document Manager (Documents)   │
│└─────────────────────────┬────────────────────────────────┘
                          │ HTTP REST
┌─────────────────────────▼────────────────────────────────┐
│              FASTAPI BACKEND (:8000)                     │
│                                                          │
│  /documents/upload  /documents/  /documents/{id}  /query │
│                                                          │
│  ┌──────────┐  ┌────────────┐  ┌──────────────────────┐  │
│  │loaders.py│  │embeddings.py│  │      rag.py          │  │
│  │PDF/DOCX/ │  │Sentence    │  │ChromaDB Retrieval +  │  │
│  │TXT Parser│  │Transformers│  │Groq API Generation   │  │
│  │          │  │(MiniLM)    │  │                      │  │
│  └──────────┘  └─────┬──────┘  └──────────────────────┘  │
│                      │                                    │
│               ┌──────▼──────┐                            │
│               │  ChromaDB   │  (saved to vectorstore/)   │
│               └─────────────┘                            │
└──────────────────────────────────────────────────────────┘
```

### RAG Pipeline Flow

```
User Question
    │
    ▼
Embed question (all-MiniLM-L6-v2)
    │
    ▼
ChromaDB similarity_search → Top-5 relevant chunks
    │
    ▼
Build context prompt
    │
    ▼
Groq API (Llama 3.3 70B) → Answer
    │
    ▼
Return: { answer, sources: [{filename, page, preview}] }
```

---

## 🗂️ Project Structure

```
documind-ai/
│
├── backend/
│   ├── app.py           # FastAPI REST API (upload, list, delete, query)
│   ├── rag.py           # RAG pipeline (retrieval + Groq API)
│   ├── embeddings.py    # Sentence Transformer + ChromaDB vector store
│   └── loaders.py       # Document parsers (PDF/DOCX/TXT)
│
├── frontend/
│   ├── .streamlit/
│   │   └── config.toml  # Dark violet theme
│   └── src/
│       ├── main.py               # Streamlit Chat page
│       ├── api_client.py         # HTTP client for backend
│       └── pages/
│           └── 1_📄_Documents.py # Document Manager page
│
├── documents/           # Uploaded raw files (auto-created)
│   └── sample_docs/     # Sample documents for testing
│
├── vectorstore/         # ChromaDB files (auto-created)
│
├── requirements.txt
├── .env
└── README.md
```

---

## ⚙️ Setup Instructions

### Prerequisites

- Python 3.10+
- Groq API Key (get a free key at [console.groq.com](https://console.groq.com/))
- Git

### Step 1 — Clone the Repository

```bash
git clone https://github.com/your-username/documind-ai.git
cd documind-ai
```

### Step 2 — Configure Environment

Create a `.env` file in the root folder and add your Groq API Key:

```env
GROQ_API_KEY=gsk_your_key_here
GROQ_MODEL=llama-3.3-70b-versatile
UPLOAD_DIR=./documents
VECTORSTORE_DIR=./vectorstore
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
MAX_FILE_SIZE_MB=20
CHUNK_SIZE=800
CHUNK_OVERLAP=100
TOP_K_CHUNKS=5
BACKEND_URL=http://localhost:8000
```

### Step 3 — Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Start the Backend

```bash
cd backend
python app.py
```
- Backend runs at: `http://localhost:8000`
- Swagger docs at: `http://localhost:8000/docs`

### Step 5 — Start the Frontend

Open a new terminal window:

```bash
cd frontend
streamlit run src/main.py
```
- App opens at: `http://localhost:8501`

### Step 6 — Deploy to Render

1. Go to [Render Dashboard](https://dashboard.render.com/) and create a new **Web Service**.
2. Connect your GitHub repository.
3. Add the following **Environment Variables**:
   - `PYTHON_VERSION`: `3.11.9`
   - `GROQ_API_KEY`: `your_groq_api_key_here`
4. Set the **Build Command**:
   ```bash
   pip install -r requirements.txt
   ```
5. Set the **Start Command**:
   ```bash
   cd backend && uvicorn app:app --host 0.0.0.0 --port $PORT
   ```
   *(Note: If your code is inside a subfolder, set the Root Directory in Render to that folder).*


---

## 🌍 Environment Variables

| Variable | Default | Description |
|---|---|---|
| `GROQ_API_KEY` | (None) | Groq API Key |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Groq model name |
| `UPLOAD_DIR` | `./documents` | Directory for uploaded files |
| `VECTORSTORE_DIR` | `./vectorstore` | Directory for ChromaDB store |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | HuggingFace embedding model |
| `MAX_FILE_SIZE_MB` | `20` | Maximum file size per upload |
| `CHUNK_SIZE` | `800` | Text chunk size (tokens) |
| `CHUNK_OVERLAP` | `100` | Overlap between consecutive chunks |
| `TOP_K_CHUNKS` | `5` | Number of chunks to retrieve per query |
| `BACKEND_URL` | `http://localhost:8000` | Backend URL (used by Streamlit) |

---

## 🧪 Sample Documents & Test Queries

Four sample documents are included in `documents/sample_docs/`:

| File | Content |
|---|---|
| `data_science_internship_jd.txt` | Data science intern job description with responsibilities |
| `company_hr_policy.txt` | HR policy — leave, attendance, benefits, code of conduct |
| `technical_faq.txt` | FAQ — setup, architecture, troubleshooting |
| `product_manual.txt` | GPS device manual — specs, installation, alerts |

### Sample Questions to Try

```
"What are the responsibilities of a data science intern?"
"How many days of annual leave do employees get?"
"What is the maternity leave policy?"
"How does the RAG pipeline work?"
"What is the operating temperature range of SmartTrack Pro?"
```

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/documents/upload` | Upload files (multipart/form-data) |
| `GET` | `/documents/` | List all documents |
| `DELETE` | `/documents/{doc_id}` | Delete document + embeddings |
| `POST` | `/query` | Ask a question |

---

## 🎯 Assumptions Made

1. **Local deployment with API services** — No local authentication. Designed as a single-user tool.
2. **Text-based PDFs only** — Scanned/image-only PDFs are not supported (no OCR).
3. **English language** — The embedding model and default LLMs are optimized for English text.
4. **ChromaDB over FAISS** — ChromaDB was chosen as the primary vector store for its clean PersistentClient structure.

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Backend | Python, FastAPI, Uvicorn |
| Document Processing | pdfplumber, PyPDF2, python-docx, chardet |
| Chunking | LangChain RecursiveCharacterTextSplitter |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 |
| Vector Store | ChromaDB |
| LLM | Groq API (Llama 3.3) |
| Frontend | Streamlit |
#   D o c u M i n d - A I  
 