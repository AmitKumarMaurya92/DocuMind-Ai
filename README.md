# DocuMind AI - Intelligent Document Question Answering System

## Overview

DocuMind AI is an intelligent document question-answering system built using Retrieval-Augmented Generation (RAG). The application enables users to upload multiple documents and interact with them using natural language queries. The system extracts information from uploaded documents, retrieves relevant content, and generates accurate, context-aware responses.

The project addresses the challenge of finding information quickly when knowledge is distributed across multiple reports, manuals, policies, FAQs, and technical documents.

---

## Features

### Document Management

* Upload multiple documents
* View uploaded documents
* Support for:

  * PDF
  * DOCX
  * TXT

### Intelligent Question Answering

* Natural language querying
* Multi-document retrieval
* Context-aware answer generation
* Fast semantic search using vector embeddings

### User Interface

* Streamlit-based interactive frontend
* Chat-style question-answer interface
* Document upload and management dashboard

---

## System Architecture

User → Streamlit Frontend → FastAPI Backend → Document Processing → Text Chunking → Embedding Generation → ChromaDB Vector Store → Retriever → LLM (Groq/Ollama) → Response Generation

---

## Technology Stack

### Frontend

* Streamlit

### Backend

* FastAPI
* Uvicorn

### Retrieval Framework

* LangChain

### Vector Database

* ChromaDB

### Embedding Model

* Sentence Transformers
* all-MiniLM-L6-v2

### Large Language Model

* Groq (Llama 3.1)
* Ollama (Optional)

### Document Processing

* PyPDF
* Python-docx

---

## Project Structure

```text
DocuMind-AI/
│
├── frontend/
│   ├── .streamlit/
│   │   └── config.toml
│   └── src/
│       ├── main.py
│       ├── api_client.py
│       └── pages/
│           └── 1_📄_Documents.py
│
├── backend/
│   ├── app.py
│   ├── loaders.py
│   ├── rag.py
│   └── embeddings.py
│
├── documents/
│   └── sample_docs/
│
├── vectorstore/
├── requirements.txt
├── .env
└── README.md
```

---

## Workflow

### Step 1: Document Upload

Users upload PDF, DOCX, or TXT files through the Streamlit interface.

### Step 2: Text Extraction

The system extracts text from uploaded documents using appropriate parsers.

### Step 3: Text Chunking

Large documents are divided into smaller chunks for efficient retrieval.

### Step 4: Embedding Generation

Text chunks are converted into vector embeddings using Sentence Transformers.

### Step 5: Vector Storage

Embeddings and metadata are stored in ChromaDB.

### Step 6: Query Processing

User questions are converted into embeddings and matched against stored document embeddings.

### Step 7: Retrieval

Top relevant chunks are retrieved using similarity search.

### Step 8: Answer Generation

The retrieved context is passed to the LLM, which generates a concise and accurate answer.

---

## Setup Instructions

### Clone Repository

```bash
git clone https://github.com/AmitKumarMaurya92/DocuMind-AI.git
cd DocuMind-AI
```

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Virtual Environment

Windows:

```bash
venv\Scripts\activate
```

Linux/Mac:

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file:

```env
GROQ_API_KEY=your_groq_api_key
```

---

## Run Backend

```bash
cd backend
python app.py
```

Backend URL:

```text
http://localhost:8000
```

---

## Run Frontend

```bash
cd frontend
streamlit run src/main.py
```

Frontend URL:

```text
http://localhost:8501
```

---

## Sample Questions

* What are the responsibilities of a data science intern?
* What is the internship stipend?
* What is the remote work policy?
* How often are passwords changed?
* What benefits are provided to employees?
* Compare intern leave policy and employee leave policy.
* How does the company support employee learning?

---

## Assumptions Made

1. Uploaded documents contain machine-readable text.
2. Documents are primarily in English.
3. Users ask questions related to uploaded documents.
4. Uploaded files are valid PDF, DOCX, or TXT formats.
5. Internet access is available when using Groq.
