import sys
import os
import time

import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from api_client import upload_documents, list_documents, delete_document, health_check

st.set_page_config(
    page_title="DocuMind AI — Documents",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.stApp { background: linear-gradient(135deg, #0F172A 0%, #1a1040 100%); }
.page-title {
    font-size: 2rem; font-weight: 700;
    background: linear-gradient(135deg, #A78BFA, #60A5FA);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.upload-zone {
    border: 2px dashed rgba(124, 58, 237, 0.4); border-radius: 16px;
    padding: 2rem; text-align: center; background: rgba(124, 58, 237, 0.05); margin-bottom: 1.5rem;
}
.doc-card {
    background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(124, 58, 237, 0.2);
    border-radius: 14px; padding: 1rem 1.2rem; margin-bottom: 0.75rem; backdrop-filter: blur(10px);
}
.doc-card .doc-name { font-weight: 600; color: #E2E8F0; font-size: 1rem; }
.doc-card .doc-meta { font-size: 0.78rem; color: #64748B; margin-top: 0.3rem; }
.status-pill { display: inline-block; border-radius: 20px; padding: 0.2rem 0.75rem; font-size: 0.75rem; font-weight: 600; margin-left: 0.5rem; }
.status-ready    { background: rgba(52,211,153,0.15); color: #34D399; border: 1px solid rgba(52,211,153,0.3); }
.status-processing { background: rgba(251,191,36,0.15); color: #FBBF24; border: 1px solid rgba(251,191,36,0.3); }
.status-pending  { background: rgba(148,163,184,0.1); color: #94A3B8; border: 1px solid rgba(148,163,184,0.2); }
.status-error    { background: rgba(248,113,113,0.15); color: #F87171; border: 1px solid rgba(248,113,113,0.3); }
.stat-bar { display: flex; gap: 1rem; margin-bottom: 1.5rem; }
.stat-item {
    flex: 1; background: rgba(30,41,59,0.7); border: 1px solid rgba(124,58,237,0.2);
    border-radius: 12px; padding: 1rem; text-align: center;
}
.stat-item .s-val { font-size: 1.8rem; font-weight: 700; color: #A78BFA; }
.stat-item .s-label { font-size: 0.75rem; color: #64748B; margin-top: 0.2rem; }
.section-divider { border: none; border-top: 1px solid rgba(124,58,237,0.12); margin: 1.25rem 0; }
[data-testid="stSidebar"] {
    background: rgba(15, 23, 42, 0.95) !important;
    border-right: 1px solid rgba(124, 58, 237, 0.2) !important;
}
</style>
""", unsafe_allow_html=True)

if "documents" not in st.session_state:
    st.session_state.documents = []
if "delete_confirm" not in st.session_state:
    st.session_state.delete_confirm = None

with st.sidebar:
    st.markdown("### 🧠 DocuMind AI")
    st.page_link("main.py", label="💬 Chat", icon="🧠")
    st.markdown("---")
    health = health_check()
    if "error" in health:
        st.error("Backend offline", icon="🔴")
    else:
        st.success("Backend connected", icon="🟢")

st.markdown('<p class="page-title">📄 Document Manager</p>', unsafe_allow_html=True)
st.markdown('<p style="color:#64748B;margin-top:-0.5rem;">Upload, monitor, and manage your document library.</p>', unsafe_allow_html=True)

st.markdown("#### ⬆️ Upload Documents")
st.markdown("""
<div class="upload-zone">
    <span style="font-size:2.5rem;">📂</span>
    <p style="color:#94A3B8;margin:0.5rem 0 0 0;font-size:0.9rem;">
        Drag and drop files here or use the picker below<br>
        <span style="color:#64748B;font-size:0.8rem;">Supported: PDF · DOCX · TXT · Max 20MB per file</span>
    </p>
</div>
""", unsafe_allow_html=True)

uploaded_files = st.file_uploader(
    "Choose files",
    type=["pdf", "docx", "txt"],
    accept_multiple_files=True,
    label_visibility="collapsed",
)

if uploaded_files:
    col_up, _ = st.columns([1, 3])
    with col_up:
        upload_btn = st.button("⬆️ Upload Files", type="primary", use_container_width=True)
    if upload_btn:
        with st.spinner(f"Uploading {len(uploaded_files)} file(s)..."):
            result = upload_documents(uploaded_files)
        if "error" in result:
            st.error(f"Upload failed: {result['error']}", icon="❌")
        else:
            names = [u["filename"] for u in result.get("uploaded", [])]
            st.success(f"Uploaded: **{', '.join(names)}**. Processing in background...", icon="🚀")
            time.sleep(0.5)
            st.session_state.documents = list_documents()
            st.rerun()

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

col_title, col_refresh = st.columns([4, 1])
with col_title:
    st.markdown("#### 📚 Your Documents")
with col_refresh:
    if st.button("🔄 Refresh", use_container_width=True):
        st.session_state.documents = list_documents()
        st.rerun()

if not st.session_state.documents:
    st.session_state.documents = list_documents()

docs = st.session_state.documents

if docs:
    ready      = sum(1 for d in docs if d["status"] == "ready")
    processing = sum(1 for d in docs if d["status"] == "processing")
    total_chunks = sum(d.get("chunk_count", 0) for d in docs)

    st.markdown(f"""
    <div class="stat-bar">
        <div class="stat-item"><div class="s-val">{len(docs)}</div><div class="s-label">Total Files</div></div>
        <div class="stat-item"><div class="s-val">{ready}</div><div class="s-label">Ready</div></div>
        <div class="stat-item"><div class="s-val">{processing}</div><div class="s-label">Processing</div></div>
        <div class="stat-item"><div class="s-val">{total_chunks}</div><div class="s-label">Total Chunks</div></div>
    </div>
    """, unsafe_allow_html=True)

    has_pending = any(d["status"] in ("pending", "processing") for d in docs)
    if has_pending:
        st.info("Some documents are still processing. Refreshing shortly...", icon="🔄")
        time.sleep(3)
        st.session_state.documents = list_documents()
        st.rerun()

    pill_map = {
        "ready":      ("status-ready",      "✅ Ready"),
        "processing": ("status-processing", "⚙️ Processing"),
        "pending":    ("status-pending",    "⏳ Pending"),
        "error":      ("status-error",      "❌ Error"),
    }

    for doc in docs:
        status = doc.get("status", "pending")
        pill_cls, pill_label = pill_map.get(status, ("status-pending", status))
        size_kb = doc.get("size_bytes", 0) // 1024
        chunks = doc.get("chunk_count", 0)
        uploaded_at = doc.get("uploaded_at", "")[:10]
        error_msg = doc.get("error")

        col_info, col_action = st.columns([5, 1])
        with col_info:
            error_html = f"&nbsp;·&nbsp;<span style='color:#F87171;'>Error: {error_msg}</span>" if error_msg else ""
            st.markdown(f"""
            <div class="doc-card">
                <div class="doc-name">📄 {doc['filename']}<span class="status-pill {pill_cls}">{pill_label}</span></div>
                <div class="doc-meta">Uploaded: {uploaded_at} &nbsp;·&nbsp; Size: {size_kb} KB &nbsp;·&nbsp; Chunks: {chunks}{error_html}</div>
            </div>
            """, unsafe_allow_html=True)
        with col_action:
            st.markdown("<div style='padding-top:0.55rem'></div>", unsafe_allow_html=True)
            if st.button("🗑️", key=f"del_{doc['doc_id']}", help="Delete document"):
                st.session_state.delete_confirm = doc["doc_id"]
                st.rerun()
else:
    st.markdown("""
    <div style="text-align:center;padding:3rem;color:#475569;">
        <div style="font-size:3rem;">📭</div>
        <h3 style="color:#64748B;">No documents yet</h3>
        <p style="font-size:0.9rem;">Upload your first document above to get started.</p>
    </div>
    """, unsafe_allow_html=True)

if st.session_state.delete_confirm:
    doc_id = st.session_state.delete_confirm
    doc_info = next((d for d in docs if d["doc_id"] == doc_id), None)
    doc_name = doc_info["filename"] if doc_info else doc_id

    st.warning(f"Delete **{doc_name}**? This also removes its embeddings.", icon="🗑️")
    c1, c2, _ = st.columns([1, 1, 4])
    with c1:
        if st.button("Yes, delete", type="primary", use_container_width=True):
            with st.spinner("Deleting..."):
                result = delete_document(doc_id)
            st.session_state.delete_confirm = None
            if "error" in result:
                st.error(f"Delete failed: {result['error']}")
            else:
                st.success(f"'{doc_name}' deleted.")
                st.session_state.documents = list_documents()
                time.sleep(0.5)
                st.rerun()
    with c2:
        if st.button("Cancel", use_container_width=True):
            st.session_state.delete_confirm = None
            st.rerun()
