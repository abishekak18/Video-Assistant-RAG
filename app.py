import streamlit as st
import time
from dotenv import load_dotenv
from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarizer import summarize, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, ask_question

load_dotenv()

# ─── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Video Assistant — Meeting Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Advanced Design System & Custom CSS ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Global Theme & Design Tokens ── */
:root {
    --bg-dark: #07090e;
    --surface-glass: rgba(15, 20, 32, 0.75);
    --surface-card: rgba(22, 28, 45, 0.6);
    --surface-hover: rgba(30, 38, 60, 0.8);
    --border-glass: rgba(255, 255, 255, 0.08);
    --border-glow: rgba(124, 58, 237, 0.3);
    
    --primary-gradient: linear-gradient(135deg, #7c3aed 0%, #06b6d4 100%);
    --accent-glow: #a78bfa;
    --accent-cyan: #38bdf8;
    --accent-pink: #f472b6;
    --accent-green: #34d399;
    
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
}

/* ── Reset & Core Styles ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    background-color: var(--bg-dark) !important;
    color: var(--text-primary) !important;
}

.stApp {
    background: radial-gradient(circle at 15% 15%, rgba(124, 58, 237, 0.08) 0%, transparent 40%),
                radial-gradient(circle at 85% 85%, rgba(6, 182, 212, 0.08) 0%, transparent 40%),
                var(--bg-dark) !important;
    background-attachment: fixed !important;
}

/* ── Typography Override ── */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
    color: var(--text-primary) !important;
}

/* ── Hero Title Banner ── */
.hero-container {
    padding: 2.5rem 2rem 1.5rem 2rem;
    background: linear-gradient(135deg, rgba(124, 58, 237, 0.12) 0%, rgba(6, 182, 212, 0.05) 100%);
    border: 1px solid rgba(124, 58, 237, 0.25);
    border-radius: 20px;
    backdrop-filter: blur(16px);
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
    box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.5);
}

.hero-container::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 2px;
    background: var(--primary-gradient);
}

.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.35rem 0.85rem;
    background: rgba(124, 58, 237, 0.18);
    border: 1px solid rgba(167, 139, 250, 0.3);
    border-radius: 100px;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--accent-glow);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 1rem;
}

.hero-title-text {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: clamp(2.2rem, 4vw, 3.2rem);
    font-weight: 800;
    line-height: 1.15;
    background: linear-gradient(135deg, #ffffff 30%, var(--accent-glow) 70%, var(--accent-cyan) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
}

.hero-subtitle {
    font-size: 1rem;
    color: var(--text-secondary);
    margin-top: 0.6rem;
    max-width: 650px;
    line-height: 1.6;
}

/* ── Modern Glass Cards ── */
.glass-card {
    background: var(--surface-card);
    border: 1px solid var(--border-glass);
    border-radius: 16px;
    padding: 1.5rem;
    backdrop-filter: blur(12px);
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    height: 100%;
    position: relative;
}

.glass-card:hover {
    border-color: rgba(167, 139, 250, 0.4);
    transform: translateY(-2px);
    box-shadow: 0 12px 30px -10px rgba(124, 58, 237, 0.15);
}

.card-header-flex {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid var(--border-glass);
}

.card-title-text {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 0.875rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--accent-glow);
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.card-body-text {
    font-size: 0.925rem;
    line-height: 1.7;
    color: var(--text-primary);
}

/* ── Stat Metric Pill ── */
.metric-box {
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid var(--border-glass);
    border-radius: 12px;
    padding: 1rem 1.25rem;
    text-align: center;
}

.metric-val {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 1.75rem;
    font-weight: 800;
    color: #ffffff;
    background: var(--primary-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.metric-lbl {
    font-size: 0.75rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 0.2rem;
}

/* ── Sidebar Styling ── */
[data-testid="stSidebar"] {
    background-color: rgba(10, 14, 23, 0.95) !important;
    border-right: 1px solid var(--border-glass) !important;
}

.sidebar-brand {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 1.4rem;
    font-weight: 800;
    background: var(--primary-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* ── Inputs & Controls ── */
.stTextInput > div > div > input,
.stSelectbox > div > div {
    background: rgba(22, 28, 45, 0.8) !important;
    border: 1px solid var(--border-glass) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
    font-size: 0.9rem !important;
    transition: all 0.2s ease !important;
}

.stTextInput > div > div > input:focus,
.stSelectbox > div > div:focus {
    border-color: var(--accent-glow) !important;
    box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.25) !important;
}

/* ── Buttons ── */
.stButton > button {
    background: var(--primary-gradient) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    letter-spacing: 0.03em !important;
    padding: 0.65rem 1.4rem !important;
    box-shadow: 0 8px 20px -6px rgba(124, 58, 237, 0.5) !important;
    transition: all 0.25s ease !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 12px 25px -4px rgba(124, 58, 237, 0.7) !important;
}

.stButton > button[kind="secondary"] {
    background: rgba(30, 41, 59, 0.7) !important;
    border: 1px solid var(--border-glass) !important;
    box-shadow: none !important;
}

.stButton > button[kind="secondary"]:hover {
    background: rgba(51, 65, 85, 0.9) !important;
    color: var(--text-primary) !important;
}

/* ── Tabs Styling ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px !important;
    background-color: rgba(15, 23, 42, 0.6) !important;
    padding: 6px !important;
    border-radius: 12px !important;
    border: 1px solid var(--border-glass) !important;
}

.stTabs [data-baseweb="tab"] {
    height: 42px !important;
    border-radius: 8px !important;
    color: var(--text-secondary) !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    transition: all 0.2s !important;
    border: none !important;
}

.stTabs [aria-selected="true"] {
    background: var(--primary-gradient) !important;
    color: #ffffff !important;
}

/* ── Step Status Tracker ── */
.status-node {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.65rem 0.9rem;
    background: rgba(15, 23, 42, 0.5);
    border: 1px solid var(--border-glass);
    border-radius: 10px;
    margin-bottom: 0.5rem;
    font-size: 0.825rem;
    transition: all 0.2s ease;
}

.dot-indicator {
    width: 9px; height: 9px;
    border-radius: 50%;
    flex-shrink: 0;
}

.dot-active {
    background: var(--accent-cyan);
    box-shadow: 0 0 10px var(--accent-cyan);
    animation: glow-pulse 1.4s infinite;
}

.dot-done { background: var(--accent-green); box-shadow: 0 0 6px var(--accent-green); }
.dot-pending { background: var(--text-muted); opacity: 0.4; }

@keyframes glow-pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.4; transform: scale(0.85); }
}

/* ── Transcript Box ── */
.transcript-styled {
    background: rgba(10, 14, 23, 0.7);
    border: 1px solid var(--border-glass);
    border-radius: 12px;
    padding: 1.25rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    line-height: 1.8;
    color: #cbd5e1;
    max-height: 400px;
    overflow-y: auto;
    white-space: pre-wrap;
    word-break: break-word;
}

/* ── Scrollbars ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(148, 163, 184, 0.2); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent-glow); }
</style>
""", unsafe_allow_html=True)

# ─── Session State Initialization ─────────────────────────────────────────────
for key, default in {
    "result": None,
    "chat_history": [],
    "pipeline_done": False,
    "pipeline_steps": {},
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ─── Helper Functions ──────────────────────────────────────────────────────────
def step_css(steps: dict, key: str) -> str:
    s = steps.get(key, "pending")
    if s == "active":  return "dot-active"
    if s == "done":    return "dot-done"
    return "dot-pending"

def render_status_item(label: str, key: str, icon: str):
    css_class = step_css(st.session_state.pipeline_steps, key)
    st.markdown(f"""
    <div class="status-node">
        <div class="dot-indicator {css_class}"></div>
        <span>{icon} {label}</span>
    </div>""", unsafe_allow_html=True)

# ─── Sidebar Navigation & Controls ──────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-brand">⚡ AI Video Assistant</div>', unsafe_allow_html=True)
    st.caption("Next-Gen Meeting & Video Intelligence")
    st.markdown("---")

    st.markdown("#### 📥 Input Source")
    source = st.text_input(
        "YouTube Link or File Path",
        placeholder="https://youtube.com/watch?v=... or C:/path/file.mp4",
        help="Paste a YouTube URL or path to a local audio/video file."
    )

    language = st.selectbox(
        "Speech Model Language",
        ["english", "hinglish"],
        index=0,
        help="Select 'hinglish' if the audio contains mixed Hindi & English."
    )

    st.markdown("<br>", unsafe_allow_html=True)
    run_btn = st.button("🚀 Analyze Content", use_container_width=True)

    if st.session_state.pipeline_done:
        st.markdown("---")
        st.markdown("#### ⚙️ Pipeline Execution")
        for step_id, icon, label in [
            ("audio",      "🔊", "Audio Preparation"),
            ("transcript", "📝", "Whisper STT"),
            ("title",      "🏷️", "Title Synthesis"),
            ("summary",    "📋", "Summary Generation"),
            ("extract",    "🔍", "Key Extraction"),
            ("rag",        "🧠", "RAG Vector Index"),
        ]:
            render_status_item(label, step_id, icon)

# ─── Main Content Area ──────────────────────────────────────────────────────────

# Header Banner
st.markdown("""
<div class="hero-container">
    <div class="hero-badge">⚡ Powered by Whisper & LangChain RAG</div>
    <div class="hero-title-text">Meeting Intelligence Assistant</div>
    <div class="hero-subtitle">Transform long YouTube videos and meeting recordings into structured executive summaries, actionable insights, and an interactive AI Q&A session.</div>
</div>
""", unsafe_allow_html=True)

# ── Run Pipeline Handler ───────────────────────────────────────────────────────
if run_btn:
    if not source.strip():
        st.warning("⚠️ Please provide a valid YouTube URL or file path in the sidebar.")
    else:
        st.session_state.pipeline_done = False
        st.session_state.result = None
        st.session_state.chat_history = []
        st.session_state.pipeline_steps = {}

        status_box = st.empty()

        def set_step(key, status):
            st.session_state.pipeline_steps[key] = status

        try:
            with status_box.container():
                st.info("⚡ Pipeline actively processing... View live step progress in the sidebar.")

            set_step("audio", "active")
            chunks = process_input(source)
            set_step("audio", "done")

            set_step("transcript", "active")
            transcript = transcribe_all(chunks, language)
            set_step("transcript", "done")

            set_step("title", "active")
            title = generate_title(transcript)
            set_step("title", "done")

            set_step("summary", "active")
            summary = summarize(transcript)
            set_step("summary", "done")

            set_step("extract", "active")
            action_items = extract_action_items(transcript)
            decisions    = extract_key_decisions(transcript)
            questions    = extract_questions(transcript)
            set_step("extract", "done")

            set_step("rag", "active")
            rag_chain = build_rag_chain(transcript)
            set_step("rag", "done")

            st.session_state.result = {
                "title": title,
                "transcript": transcript,
                "summary": summary,
                "action_items": action_items,
                "key_decisions": decisions,
                "open_questions": questions,
                "rag_chain": rag_chain,
            }
            st.session_state.pipeline_done = True
            status_box.success("🎉 Analysis successfully completed!")
            time.sleep(0.6)
            status_box.empty()
            st.rerun()

        except Exception as err:
            for k in ["audio", "transcript", "title", "summary", "extract", "rag"]:
                if st.session_state.pipeline_steps.get(k) == "active":
                    st.session_state.pipeline_steps[k] = "pending"
            status_box.error(f"❌ Pipeline failed: {err}")

# ── Results Dashboard ──────────────────────────────────────────────────────────
if st.session_state.result:
    res = st.session_state.result

    # Quick Metrics Banner
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    words = len(res['transcript'].split())
    est_read_time = f"{max(1, round(words / 150))} min"

    with m_col1:
        st.markdown(f'<div class="metric-box"><div class="metric-val">{words:,}</div><div class="metric-lbl">Total Words</div></div>', unsafe_allow_html=True)
    with m_col2:
        st.markdown(f'<div class="metric-box"><div class="metric-val">{est_read_time}</div><div class="metric-lbl">Est. Read Time</div></div>', unsafe_allow_html=True)
    with m_col3:
        st.markdown(f'<div class="metric-box"><div class="metric-val">{language.capitalize()}</div><div class="metric-lbl">Audio Language</div></div>', unsafe_allow_html=True)
    with m_col4:
        st.markdown('<div class="metric-box"><div class="metric-val">RAG Ready</div><div class="metric-lbl">Vector Index</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Session Title Card
    st.markdown(f"""
    <div class="glass-card" style="margin-bottom: 1.5rem;">
        <div class="card-header-flex">
            <span class="card-title-text">📌 Generated Title</span>
            <span style="font-size:0.75rem; color:var(--text-muted);">AI Synthesized</span>
        </div>
        <div style="font-family:'Plus Jakarta Sans',sans-serif; font-size:1.35rem; font-weight:800; color:var(--text-primary)">
            {res['title']}
        </div>
    </div>""", unsafe_allow_html=True)

    # Tabs Navigation for Structured Views
    tab_overview, tab_insights, tab_transcript, tab_chat = st.tabs([
        "📊 Executive Summary",
        "⚡ Action & Key Insights",
        "📝 Full Transcript",
        "💬 Interactive RAG Chat"
    ])

    # TAB 1: Executive Summary
    with tab_overview:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="glass-card">
            <div class="card-header-flex">
                <span class="card-title-text">📋 Executive Summary</span>
            </div>
            <div class="card-body-text">{res['summary']}</div>
        </div>""", unsafe_allow_html=True)

    # TAB 2: Insights Grid
    with tab_insights:
        st.markdown("<br>", unsafe_allow_html=True)
        col_act, col_dec, col_q = st.columns(3)

        with col_act:
            st.markdown(f"""
            <div class="glass-card">
                <div class="card-header-flex">
                    <span class="card-title-text" style="color:var(--accent-cyan);">✅ Action Items</span>
                </div>
                <div class="card-body-text">{res['action_items']}</div>
            </div>""", unsafe_allow_html=True)

        with col_dec:
            st.markdown(f"""
            <div class="glass-card">
                <div class="card-header-flex">
                    <span class="card-title-text" style="color:var(--accent-glow);">🔑 Key Decisions</span>
                </div>
                <div class="card-body-text">{res['key_decisions']}</div>
            </div>""", unsafe_allow_html=True)

        with col_q:
            st.markdown(f"""
            <div class="glass-card">
                <div class="card-header-flex">
                    <span class="card-title-text" style="color:var(--accent-pink);">❓ Open Questions</span>
                </div>
                <div class="card-body-text">{res['open_questions']}</div>
            </div>""", unsafe_allow_html=True)

    # TAB 3: Transcript View
    with tab_transcript:
        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button(
            label="📥 Download Full Transcript (.txt)",
            data=res["transcript"],
            file_name=f"{res['title'].replace(' ', '_')}_transcript.txt",
            mime="text/plain",
            key="dl_transcript"
        )
        st.markdown(f'<div class="transcript-styled">{res["transcript"]}</div>', unsafe_allow_html=True)

    # TAB 4: RAG Chat
    with tab_chat:
        st.markdown("<br>", unsafe_allow_html=True)

        # Quick Question Suggestions
        st.markdown("##### 💡 Suggested Questions")
        sug_cols = st.columns(3)
        with sug_cols[0]:
            if st.button("What were the primary takeaways?", use_container_width=True, key="sug1"):
                q_text = "What were the primary takeaways from this meeting?"
                answer = ask_question(res["rag_chain"], q_text)
                st.session_state.chat_history.append({"role": "user", "content": q_text})
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
                st.rerun()
        with sug_cols[1]:
            if st.button("Who was assigned action items?", use_container_width=True, key="sug2"):
                q_text = "Who was assigned action items and what are their tasks?"
                answer = ask_question(res["rag_chain"], q_text)
                st.session_state.chat_history.append({"role": "user", "content": q_text})
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
                st.rerun()
        with sug_cols[2]:
            if st.button("Were any deadlines mentioned?", use_container_width=True, key="sug3"):
                q_text = "Were any specific deadlines mentioned in the meeting?"
                answer = ask_question(res["rag_chain"], q_text)
                st.session_state.chat_history.append({"role": "user", "content": q_text})
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # Display Chat History using native Streamlit chat bubbles
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Chat Input
        if user_prompt := st.chat_input("Ask anything about the meeting..."):
            st.session_state.chat_history.append({"role": "user", "content": user_prompt})
            with st.chat_message("user"):
                st.markdown(user_prompt)

            with st.chat_message("assistant"):
                with st.spinner("Analyzing transcript context..."):
                    response = ask_question(res["rag_chain"], user_prompt)
                    st.markdown(response)

            st.session_state.chat_history.append({"role": "assistant", "content": response})

        if st.session_state.chat_history:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️ Clear Chat History", type="secondary"):
                st.session_state.chat_history = []
                st.rerun()

else:
    # Initial Empty State
    st.markdown("""
    <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; padding:4rem 2rem; text-align:center; background:var(--surface-card); border:1px dashed var(--border-glass); border-radius:20px;">
        <div style="font-size:3.5rem; margin-bottom:1rem;">🎬</div>
        <div style="font-family:'Plus Jakarta Sans',sans-serif; font-size:1.6rem; font-weight:800; color:var(--text-primary); margin-bottom:0.5rem;">
            Ready for Video & Meeting Analysis
        </div>
        <div style="color:var(--text-secondary); font-size:0.9rem; max-width:460px; line-height:1.7; margin-bottom:2rem;">
            Paste a YouTube link or local media file path in the sidebar navigation, select your speech model language, and click <strong>Analyze Content</strong>.
        </div>
        <div style="display:flex; gap:1rem; flex-wrap:wrap; justify-content:center;">
            <span style="padding:0.4rem 0.9rem; background:rgba(124,58,237,0.15); border:1px solid rgba(124,58,237,0.3); border-radius:100px; font-size:0.75rem; font-weight:600; color:var(--accent-glow);">Whisper STT</span>
            <span style="padding:0.4rem 0.9rem; background:rgba(6,182,212,0.15); border:1px solid rgba(6,182,212,0.3); border-radius:100px; font-size:0.75rem; font-weight:600; color:var(--accent-cyan);">Mistral AI Summarizer</span>
            <span style="padding:0.4rem 0.9rem; background:rgba(52,211,153,0.15); border:1px solid rgba(52,211,153,0.3); border-radius:100px; font-size:0.75rem; font-weight:600; color:var(--accent-green);">ChromaDB RAG Q&A</span>
        </div>
    </div>""", unsafe_allow_html=True)