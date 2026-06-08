import sys
import os
import time

import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))
from api_client import health_check, list_documents, ask_question, upload_documents

st.set_page_config(
    page_title="DocuMind AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.stApp { background: linear-gradient(135deg, #0F172A 0%, #1a1040 100%); }
.hero-header { text-align: center; padding: 1.5rem 0 0.5rem 0; }
.hero-title {
    font-size: 2.4rem; font-weight: 700;
    background: linear-gradient(135deg, #A78BFA, #60A5FA, #34D399);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    margin: 0; line-height: 1.2;
}
.hero-sub { font-size: 0.95rem; color: #94A3B8; margin: 0.4rem 0 0 0; }
[data-testid="stChatMessage"] {
    background: rgba(30, 41, 59, 0.7) !important;
    border: 1px solid rgba(124, 58, 237, 0.15) !important;
    border-radius: 16px !important;
    backdrop-filter: blur(10px);
    margin-bottom: 0.5rem;
}
[data-testid="stSidebar"] {
    background: rgba(15, 23, 42, 0.95) !important;
    border-right: 1px solid rgba(124, 58, 237, 0.2) !important;
}
.source-card {
    background: rgba(124, 58, 237, 0.08);
    border: 1px solid rgba(124, 58, 237, 0.25);
    border-radius: 10px; padding: 0.75rem 1rem; margin: 0.3rem 0;
    font-size: 0.85rem; color: #CBD5E1;
}
.source-card .src-title { font-weight: 600; color: #A78BFA; margin-bottom: 0.25rem; }
.metric-row { display: flex; gap: 0.75rem; margin-bottom: 1rem; }
.metric-card {
    flex: 1; background: rgba(30, 41, 59, 0.7);
    border: 1px solid rgba(124, 58, 237, 0.2); border-radius: 12px;
    padding: 0.75rem; text-align: center;
}
.metric-card .m-val { font-size: 1.5rem; font-weight: 700; color: #A78BFA; }
.metric-card .m-label { font-size: 0.75rem; color: #64748B; margin-top: 0.2rem; }
[data-testid="stExpander"] {
    background: rgba(15, 23, 42, 0.6) !important;
    border: 1px solid rgba(124, 58, 237, 0.15) !important;
    border-radius: 10px !important;
}
.section-divider { border: none; border-top: 1px solid rgba(124, 58, 237, 0.15); margin: 0.75rem 0; }
.model-badge {
    display: inline-block; background: rgba(124, 58, 237, 0.15);
    border: 1px solid rgba(124, 58, 237, 0.3); border-radius: 20px;
    padding: 0.15rem 0.6rem; font-size: 0.75rem; color: #A78BFA; margin-left: 0.5rem;
}
.empty-state { text-align: center; padding: 3rem 2rem; color: #475569; }
.empty-state .empty-icon { font-size: 4rem; margin-bottom: 1rem; }
.empty-state h3 { color: #64748B; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "documents" not in st.session_state:
    st.session_state.documents = []
if "selected_doc_ids" not in st.session_state:
    st.session_state.selected_doc_ids = []
if "backend_ok" not in st.session_state:
    st.session_state.backend_ok = False
if "show_uploader" not in st.session_state:
    st.session_state.show_uploader = False

health = health_check()
st.session_state.backend_ok = "error" not in health

st.markdown("""
<div class="hero-header">
    <h1 class="hero-title">🧠 DocuMind AI</h1>
    <p class="hero-sub">Ask questions across your documents — powered by Groq cloud LLMs</p>
</div>
""", unsafe_allow_html=True)

if not st.session_state.backend_ok:
    st.error("Backend unreachable. Start the server: `cd backend && python app.py`", icon="🔴")

with st.sidebar:
    st.markdown("### 📁 Documents")

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown("**📤 Upload Documents**")
    uploaded_files = st.file_uploader(
        "Choose files",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        label_visibility="collapsed",
        key="sidebar_uploader",
    )
    upload_clicked = st.button(
        "⬆️ Upload Files",
        use_container_width=True,
        type="primary",
        disabled=not uploaded_files,
    )
    if upload_clicked and uploaded_files:
        with st.spinner("Uploading..."):
            result = upload_documents(uploaded_files)
        if "error" in result:
            st.error(result["error"], icon="🔴")
        else:
            count = result.get("count", 0)
            st.success(f"✅ {count} file(s) uploaded! Processing in background.")
            st.session_state.documents = list_documents()
            st.rerun()


    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    col_r, col_p = st.columns([2, 1])
    with col_r:
        if st.button("🔄 Refresh", use_container_width=True):
            st.session_state.documents = list_documents()
            st.rerun()
    with col_p:
        st.page_link("pages/1_📄_Documents.py", label="Manage", icon="⚙️")

    if not st.session_state.documents:
        st.session_state.documents = list_documents()

    docs = st.session_state.documents
    ready_docs = [d for d in docs if d["status"] == "ready"]

    total = len(docs)
    ready = len(ready_docs)
    processing = len([d for d in docs if d["status"] == "processing"])

    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-card"><div class="m-val">{total}</div><div class="m-label">Total</div></div>
        <div class="metric-card"><div class="m-val">{ready}</div><div class="m-label">Ready</div></div>
        <div class="metric-card"><div class="m-val">{processing}</div><div class="m-label">Processing</div></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    if not docs:
        st.markdown('<p style="color:#475569;font-size:0.85rem;">No documents yet. Upload files above to get started.</p>', unsafe_allow_html=True)
    else:
        def status_icon(s):
            return {"ready": "🟢", "processing": "🟡", "pending": "⚪", "error": "🔴"}.get(s, "⚫")

        st.markdown("**Filter Q&A by document:**")
        selected_ids = []
        for doc in docs:
            label = f"{status_icon(doc['status'])} {doc['filename'][:28]}"
            checked = st.checkbox(
                label,
                key=f"select_{doc['doc_id']}",
                disabled=(doc["status"] != "ready"),
                help=f"Status: {doc['status']} | Chunks: {doc.get('chunk_count', 0)}",
            )
            if checked:
                selected_ids.append(doc["doc_id"])
        st.session_state.selected_doc_ids = selected_ids or None

        if selected_ids:
            st.info(f"Searching {len(selected_ids)} selected document(s)", icon="🔍")

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown('<p style="color:#475569;font-size:0.75rem;text-align:center;">Powered by Groq · ChromaDB · LangChain</p>', unsafe_allow_html=True)

with st.container():
    if not st.session_state.messages:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">💬</div>
            <h3>Start a conversation</h3>
            <p style="color:#475569;font-size:0.9rem;">
                Upload documents via <b>Manage</b> in the sidebar, then ask anything about their content.
            </p>
            <p style="color:#4B5563;font-size:0.8rem;margin-top:1rem;">
                💡 Try: <i>"What are the main responsibilities of a data science intern?"</i>
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "🧠"):
                st.markdown(msg["content"])
                if msg["role"] == "assistant" and msg.get("sources"):
                    with st.expander(f"📎 {len(msg['sources'])} Source(s)", expanded=False):
                        for src in msg["sources"]:
                            page_info = f" · Page {src['page']}" if src.get("page") else ""
                            st.markdown(f'<div class="source-card"><div class="src-title">📄 {src["filename"]}{page_info}</div><div>{src["preview"]}</div></div>', unsafe_allow_html=True)
                if msg["role"] == "assistant" and msg.get("model"):
                    st.markdown(f'<span class="model-badge">🤖 {msg["model"]}</span>', unsafe_allow_html=True)

attach_col, chat_col = st.columns([1, 12])
with attach_col:
    st.markdown("""
    <style>
    div[data-testid="column"]:first-child .stButton button {
        background: rgba(124, 58, 237, 0.2);
        border: 1px solid rgba(124, 58, 237, 0.5);
        border-radius: 50%;
        color: #A78BFA;
        font-size: 1.3rem;
        font-weight: 700;
        width: 42px;
        height: 42px;
        padding: 0;
        line-height: 1;
        transition: all 0.2s;
    }
    div[data-testid="column"]:first-child .stButton button:hover {
        background: rgba(124, 58, 237, 0.4);
        border-color: #A78BFA;
        transform: scale(1.1);
    }
    </style>
    """, unsafe_allow_html=True)
    if st.button("＋", key="attach_btn", help="Upload a document"):
        st.session_state.show_uploader = not st.session_state.show_uploader

if st.session_state.show_uploader:
    with st.container():
        st.markdown("""
        <div style="background:rgba(30,41,59,0.9);border:1px solid rgba(124,58,237,0.3);
        border-radius:14px;padding:1rem 1.2rem;margin-bottom:0.5rem;">
        <p style="color:#A78BFA;font-weight:600;margin:0 0 0.5rem 0;font-size:0.9rem;">📎 Attach Documents</p>
        </div>
        """, unsafe_allow_html=True)
        inline_files = st.file_uploader(
            "Choose PDF, DOCX or TXT files",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True,
            key="inline_uploader",
        )
        if inline_files:
            if st.button("⬆️ Upload & Process", type="primary", key="inline_upload_btn"):
                with st.spinner("Uploading..."):
                    result = upload_documents(inline_files)
                if "error" in result:
                    st.error(result["error"], icon="🔴")
                else:
                    count = result.get("count", 0)
                    st.success(f"✅ {count} file(s) uploaded! Processing in background.")
                    st.session_state.documents = list_documents()
                    st.session_state.show_uploader = False
                    st.rerun()

question = st.chat_input("Ask a question about your documents...", disabled=not st.session_state.backend_ok)

if question:
    st.session_state.documents = list_documents()
    ready_docs = [d for d in st.session_state.documents if d["status"] == "ready"]
    
    if not ready_docs:
        st.warning("No documents are ready yet. Please upload and wait for processing.", icon="📂")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": question, "sources": [], "model": None})

    with st.chat_message("user", avatar="🧑"):
        st.markdown(question)

    with st.chat_message("assistant", avatar="🧠"):
        with st.spinner("Thinking..."):
            result = ask_question(question=question, doc_ids=st.session_state.selected_doc_ids)

        if "error" in result:
            answer = f"❌ {result['error']}"
            sources, model = [], None
        else:
            answer = result.get("answer", "No answer returned.")
            sources = result.get("sources", [])
            model = result.get("model", "")

        st.markdown(answer)

        if sources:
            with st.expander(f"📎 {len(sources)} Source(s)", expanded=False):
                for src in sources:
                    page_info = f" · Page {src['page']}" if src.get("page") else ""
                    st.markdown(f'<div class="source-card"><div class="src-title">📄 {src["filename"]}{page_info}</div><div>{src["preview"]}</div></div>', unsafe_allow_html=True)

        if model:
            st.markdown(f'<span class="model-badge">🤖 {model}</span>', unsafe_allow_html=True)

    st.session_state.messages.append({"role": "assistant", "content": answer, "sources": sources, "model": model})
