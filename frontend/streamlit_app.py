"""
Streamlit Web Application for Hybrid RAG Networking Assistant.
Provides interactive question answering, multi-channel retrieval diagnostics,
citation verification previews, and retrieval parameter tuning.
"""
import streamlit as st
import requests
import json
import time

# Page Configuration
st.set_page_config(
    page_title="NetRAG — Hybrid Networking Assistant",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for polished appearance
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #94a3b8;
        margin-bottom: 1.5rem;
    }
    .citation-badge {
        display: inline-block;
        background-color: #1e293b;
        color: #38bdf8;
        border: 1px solid #334155;
        border-radius: 6px;
        padding: 3px 8px;
        font-size: 0.8rem;
        margin: 2px;
    }
    .score-card {
        background-color: #0f172a;
        border-radius: 8px;
        border: 1px solid #1e293b;
        padding: 12px;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

API_BASE_URL = "http://localhost:8000/api"

# Header
st.markdown('<div class="main-header">🌐 NetRAG — Production Hybrid RAG Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Specialized Computer Networking Knowledge Base • BM25 + Qdrant Dense Vector + RRF + Cross-Encoder Reranking</div>', unsafe_allow_html=True)

# Sidebar Controls
with st.sidebar:
    st.header("⚙️ Retrieval Settings")
    retrieval_mode = st.selectbox(
        "Retrieval Algorithm",
        options=["hybrid", "bm25", "vector"],
        index=0,
        help="Select hybrid (BM25 + Qdrant RRF) or individual channel baselines."
    )
    enable_rerank = st.toggle("Enable Cross-Encoder Reranker", value=True)
    top_k = st.slider("Top Evidence Passages (Top-K)", min_value=1, max_value=10, value=4)
    
    topic_filter = st.selectbox(
        "Topic Filter (Optional)",
        options=["All Topics", "DNS", "DHCP", "TCP/IP", "Subnetting", "VLANs", "Routing", "Troubleshooting", "Application Layer & TLS", "Security", "Data Center", "Configuration"]
    )
    topic_arg = None if topic_filter == "All Topics" else topic_filter

    st.divider()
    st.markdown("### 📊 Architecture Stack")
    st.markdown("""
    - **Keyword**: BM25 Okapi (Technical Tokenizer)
    - **Vector**: Qdrant (Cosine 384-dim)
    - **Fusion**: Reciprocal Rank Fusion ($k=60$)
    - **Reranker**: Cross-Encoder (Proximity & Exact match)
    - **Grounding**: Strict Citation Grammar
    """)

    st.divider()
    # Check backend health
    try:
        health_resp = requests.get(f"{API_BASE_URL}/health", timeout=2)
        if health_resp.status_code == 200:
            st.success("🟢 API Backend: Online")
        else:
            st.warning("🟡 API Backend: Degraded")
    except Exception:
        st.info("ℹ️ Local Mode (Direct Pipeline execution)")

# Sample questions selector
SAMPLE_QUESTIONS = [
    "Select an example question...",
    "Why is /31 subnet permitted on point-to-point links under RFC 3021?",
    "What causes an MTU Black Hole and how does TCP MSS clamping remediate it?",
    "How does HTTP/3 with QUIC eliminate Transport-Layer Head-of-Line blocking?",
    "What is the difference between an A record and an AAAA record in DNS?",
    "What Wireshark command filter captures all TCP SYN and RST flags traversing port 443?",
    "What are the four congestion control algorithms specified in RFC 5681?",
    "What are the recommended fertilizer types for growing hydroponic tomatoes? (Test Abstention)"
]

col1, col2 = st.columns([3, 1])
with col1:
    selected_sample = st.selectbox("💡 Try a Pre-configured Technical Query:", SAMPLE_QUESTIONS)
with col2:
    st.write("")
    st.write("")
    run_sample = st.button("Load Query", use_container_width=True)

query_input = st.text_input(
    "Enter Networking Technical Question:",
    value=selected_sample if selected_sample != "Select an example question..." else "",
    placeholder="e.g. Under what conditions does DNS fall back from UDP port 53 to TCP port 53?"
)

if st.button("🚀 Search & Answer", type="primary", use_container_width=True) and query_input.strip():
    with st.spinner("Executing hybrid retrieval, reranking, and grounded generation..."):
        t0 = time.time()
        payload = {
            "query": query_input.strip(),
            "mode": retrieval_mode,
            "enable_rerank": enable_rerank,
            "top_k": top_k,
            "topic_filter": topic_arg
        }

        # Try API, fallback to local pipeline direct call
        resp_data = None
        try:
            r = requests.post(f"{API_BASE_URL}/query", json=payload, timeout=20)
            if r.status_code == 200:
                resp_data = r.json()
        except Exception:
            pass

        if not resp_data:
            # Fallback direct call inside Streamlit
            from app.api.routes_query import get_pipeline, QueryRequest, answer_question
            pipe = get_pipeline()
            req = QueryRequest(
                query=query_input.strip(),
                mode=retrieval_mode,
                enable_rerank=enable_rerank,
                top_k=top_k,
                topic_filter=topic_arg
            )
            res = answer_question(req, pipe)
            resp_data = res.dict()

        elapsed = resp_data.get("latency_ms", round((time.time() - t0) * 1000, 2))

        # Display Result
        st.subheader("💡 Grounded Answer")
        if resp_data.get("abstention"):
            st.warning(f"⚠️ {resp_data['answer']}")
        else:
            st.markdown(f"**{resp_data['answer']}**")

        # Citations pill badges
        citations = resp_data.get("citations", [])
        if citations:
            st.write("##### 📌 Verified Citations:")
            c_html = ""
            for c in citations:
                c_html += f'<span class="citation-badge">📄 {c["doc_id"]} &gt; {c["section"]}</span> '
            st.markdown(c_html, unsafe_allow_html=True)

        st.caption(f"⏱️ Retrieval & Generation Latency: **{elapsed} ms** | Mode: **{retrieval_mode.upper()}** | Rerank: **{'ON' if enable_rerank else 'OFF'}**")

        st.divider()

        # Detailed Inspection Tabs
        tab1, tab2, tab3 = st.tabs(["📑 Retrieved Evidence Passages", "🔬 Retrieval Signals & Scores", "📊 Context Budget Stats"])

        with tab1:
            passages = resp_data.get("selected_passages", [])
            for i, p in enumerate(passages, 1):
                with st.expander(f"Passage [{i}]: {p.get('title')} — {p.get('section')} (ID: {p.get('chunk_id')})", expanded=(i == 1)):
                    st.markdown(f"**Topic:** `{p.get('topic')}` | **Source URL:** [{p.get('source_url')}]({p.get('source_url')})")
                    st.code(p.get("content", ""), language="markdown")

        with tab2:
            st.markdown("#### Multi-Channel Scoring Diagnostics")
            for i, p in enumerate(resp_data.get("selected_passages", []), 1):
                st.markdown(f"""
                <div class="score-card">
                    <b>[{i}] {p.get('chunk_id')}</b> — <i>{p.get('section')}</i><br>
                    • <b>RRF Score:</b> <code>{p.get('rrf_score', 'N/A')}</code><br>
                    • <b>Vector Score (Cosine):</b> <code>{p.get('vector_score', 'N/A')}</code> (Rank #{p.get('vector_rank', 'N/A')})<br>
                    • <b>BM25 Score:</b> <code>{p.get('bm25_score', 'N/A')}</code> (Rank #{p.get('bm25_rank', 'N/A')})<br>
                    • <b>Rerank Score:</b> <code>{p.get('rerank_score', 'N/A')}</code>
                </div>
                """, unsafe_allow_html=True)

        with tab3:
            stats = resp_data.get("context_stats", {})
            st.json(stats)
