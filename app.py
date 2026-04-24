
"""
app.py  —  SENA: 3D Printing Lab Assistant
Colorful, polished Streamlit UI + RAG + Gemini Flash
Streamlit Cloud ready (reads GOOGLE_API_KEY from st.secrets)
"""

import streamlit as st
from rag_pipeline import SENARagPipeline

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="SENA · 3D Lab Assistant",
    page_icon="🖨️",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
#  COLOR PALETTE (filament-inspired split-complementary)
#  --orange  #ff6b2b   hot nozzle  →  primary action / user
#  --cyan    #00d4e8   LCD blue    →  assistant / RAG badge
#  --lime    #a3e635   extrusion   →  success / online
#  --pink    #f472b6   filament 4  →  highlight / welcome
#  --base    #0b0c10   dark lab    →  background
#  --surface #13151c   panels
#  --card    #1c1f2b   bubbles
# ─────────────────────────────────────────────────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --orange:  #ff6b2b;
    --cyan:    #00d4e8;
    --lime:    #a3e635;
    --pink:    #f472b6;
    --violet:  #a78bfa;
    --base:    #0b0c10;
    --surface: #13151c;
    --card:    #1c1f2b;
    --border:  rgba(255,255,255,0.07);
    --text:    #eef0f8;
    --muted:   #4a5272;
}

*, *::before, *::after { box-sizing: border-box; }

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    background: var(--base) !important;
    font-family: 'Outfit', sans-serif !important;
    color: var(--text) !important;
}

/* Mesh gradient background */
[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(ellipse 55% 45% at 0% 0%,   #2a1200bb 0%, transparent 65%),
        radial-gradient(ellipse 40% 35% at 100% 0%,  #001a2abb 0%, transparent 65%),
        radial-gradient(ellipse 35% 30% at 50% 100%, #0a001abb 0%, transparent 65%),
        var(--base) !important;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"] { display: none !important; }

.main .block-container {
    max-width: 800px !important;
    padding: 0 1.4rem 7rem !important;
    margin: 0 auto !important;
}

/* ══════════════════════════════════════════════════
   HEADER
══════════════════════════════════════════════════ */
.prism-header {
    padding: 1.8rem 0 0.8rem;
    animation: fadeDown 0.6s ease both;
}
.prism-top {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 0.6rem;
}
.prism-icon-wrap {
    width: 52px; height: 52px;
    border-radius: 14px;
    background: linear-gradient(135deg, #ff6b2b, #ff9a5c);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.6rem;
    box-shadow: 0 0 24px #ff6b2b55, 0 4px 12px #0008;
    flex-shrink: 0;
    animation: glowPulse 3s ease-in-out infinite;
}
.prism-title-block {}
.prism-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.55rem;
    font-weight: 700;
    letter-spacing: -0.5px;
    background: linear-gradient(90deg, #ff6b2b 0%, #f472b6 50%, #a78bfa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.15;
}
.prism-subtitle {
    font-size: 0.72rem;
    color: var(--muted);
    letter-spacing: 0.2em;
    text-transform: uppercase;
    font-family: 'JetBrains Mono', monospace;
    margin-top: 0.1rem;
}

/* Filament color dots */
.filament-dots {
    display: flex;
    gap: 6px;
    align-items: center;
    margin-top: 0.5rem;
}
.fdot {
    width: 10px; height: 10px;
    border-radius: 50%;
    box-shadow: 0 0 8px currentColor;
}

/* Status chips row */
.status-row {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin-top: 0.6rem;
}
.chip {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 0.22rem 0.7rem;
    border-radius: 99px;
    font-size: 0.7rem;
    font-family: 'JetBrains Mono', monospace;
    border: 1px solid;
    animation: fadeIn 0.5s ease both;
}
.chip-orange { background:#ff6b2b18; border-color:#ff6b2b55; color:#ff6b2b; }
.chip-cyan   { background:#00d4e818; border-color:#00d4e855; color:#00d4e8; }
.chip-lime   { background:#a3e63518; border-color:#a3e63555; color:#a3e635; }
.chip-pink   { background:#f472b618; border-color:#f472b655; color:#f472b6; }
.chip-violet { background:#a78bfa18; border-color:#a78bfa55; color:#a78bfa; }

.chip-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: currentColor;
}

.divider-gradient {
    height: 1px;
    background: linear-gradient(90deg, transparent, #ff6b2b44, #f472b644, #a78bfa44, transparent);
    margin: 0.8rem 0 1rem;
}

/* ══════════════════════════════════════════════════
   QUICK PROMPT CHIPS
══════════════════════════════════════════════════ */
.quick-prompts {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin-bottom: 1.2rem;
    animation: fadeIn 0.7s ease 0.3s both;
}
.qp-chip {
    padding: 0.35rem 0.85rem;
    border-radius: 99px;
    font-size: 0.78rem;
    background: var(--card);
    border: 1px solid var(--border);
    color: var(--text);
    cursor: pointer;
    transition: all 0.2s;
    white-space: nowrap;
}
.qp-chip:hover {
    border-color: var(--orange);
    color: var(--orange);
    background: #ff6b2b0f;
    transform: translateY(-1px);
}

/* ══════════════════════════════════════════════════
   CHAT MESSAGES
══════════════════════════════════════════════════ */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0.2rem 0 !important;
    animation: fadeUp 0.35s ease both;
}

/* User bubble — orange */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) .stChatMessageContent {
    background: linear-gradient(135deg, #2a1400 0%, #1e0f00 100%) !important;
    border: 1px solid #ff6b2b44 !important;
    border-radius: 18px 18px 4px 18px !important;
    padding: 0.85rem 1.15rem !important;
    color: var(--text) !important;
    box-shadow: 0 4px 20px #ff6b2b1a, inset 0 1px 0 #ff6b2b22 !important;
    max-width: 82% !important;
    margin-left: auto !important;
}

/* Assistant bubble — cyan accent */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) .stChatMessageContent {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-left: 3px solid var(--cyan) !important;
    border-radius: 4px 18px 18px 18px !important;
    padding: 0.9rem 1.2rem !important;
    color: var(--text) !important;
    max-width: 88% !important;
    box-shadow: 0 4px 20px #00d4e810 !important;
}

/* Avatars */
[data-testid="chatAvatarIcon-user"] {
    background: linear-gradient(135deg, var(--orange), #ff9a5c) !important;
    border-radius: 50% !important;
    box-shadow: 0 0 12px #ff6b2b55 !important;
}
[data-testid="chatAvatarIcon-assistant"] {
    background: linear-gradient(135deg, #00203a, #001a26) !important;
    border: 1px solid var(--cyan) !important;
    border-radius: 10px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.9rem !important;
    box-shadow: 0 0 12px #00d4e830 !important;
}

/* ══════════════════════════════════════════════════
   SOURCE BADGE
══════════════════════════════════════════════════ */
.source-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 0.7rem;
    font-family: 'JetBrains Mono', monospace;
    padding: 0.2rem 0.65rem;
    border-radius: 99px;
    margin-top: 0.5rem;
    animation: fadeIn 0.3s ease both;
}
.badge-manual {
    background: #00d4e818;
    border: 1px solid #00d4e844;
    color: var(--cyan);
}
.badge-ai {
    background: #a78bfa18;
    border: 1px solid #a78bfa44;
    color: var(--violet);
}
.badge-dot { width:5px; height:5px; border-radius:50%; background:currentColor; }

/* ══════════════════════════════════════════════════
   EMPTY STATE
══════════════════════════════════════════════════ */
.empty-state {
    text-align: center;
    padding: 3rem 1rem 2rem;
    animation: fadeIn 0.6s ease both;
}
.empty-icon { font-size: 3rem; margin-bottom: 0.8rem; }
.empty-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #8892a8;
    margin-bottom: 1.2rem;
}
.suggest-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.6rem;
    max-width: 500px;
    margin: 0 auto;
}
.suggest-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 0.8rem 1rem;
    text-align: left;
    transition: all 0.2s;
}
.suggest-card:hover {
    border-color: var(--orange);
    transform: translateY(-2px);
}
.suggest-icon { font-size: 1.2rem; margin-bottom: 0.3rem; }
.suggest-text { font-size: 0.78rem; color: #8892a8; line-height: 1.4; }

/* ══════════════════════════════════════════════════
   INPUT BAR
══════════════════════════════════════════════════ */
[data-testid="stBottom"] {
    background: linear-gradient(to top, var(--base) 80%, transparent) !important;
    padding: 1rem 1.5rem !important;
}
[data-testid="stChatInput"] {
    background: var(--surface) !important;
    border: 1.5px solid #ff6b2b33 !important;
    border-radius: 16px !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: var(--orange) !important;
    box-shadow: 0 0 0 3px #ff6b2b1a, 0 0 20px #ff6b2b12 !important;
}
[data-testid="stChatInput"] textarea {
    color: var(--text) !important;
    background: transparent !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.93rem !important;
}
[data-testid="stChatInput"] textarea::placeholder { color: var(--muted) !important; }
[data-testid="stChatInputSubmitButton"] button {
    background: linear-gradient(135deg, var(--orange), #ff9a5c) !important;
    border: none !important;
    border-radius: 12px !important;
    transition: all 0.2s !important;
    box-shadow: 0 0 12px #ff6b2b44 !important;
}
[data-testid="stChatInputSubmitButton"] button:hover {
    transform: scale(1.08) !important;
    box-shadow: 0 0 20px #ff6b2b66 !important;
}

/* ══════════════════════════════════════════════════
   SIDEBAR
══════════════════════════════════════════════════ */
[data-testid="stSidebar"] {
    background: #0c0d12 !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] label { color: var(--text) !important; font-size: 0.88rem !important; }
[data-testid="stSidebar"] p, [data-testid="stSidebar"] small { color: var(--muted) !important; }

[data-testid="stSidebar"] .stTextInput input {
    background: var(--surface) !important;
    border: 1px solid #ff6b2b33 !important;
    border-radius: 10px !important;
    color: var(--text) !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.88rem !important;
    transition: border-color 0.2s !important;
}
[data-testid="stSidebar"] .stTextInput input:focus {
    border-color: var(--orange) !important;
    box-shadow: 0 0 0 2px #ff6b2b1a !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    background: var(--surface) !important;
    border: 2px dashed #00d4e833 !important;
    border-radius: 12px !important;
    transition: border-color 0.2s !important;
}
[data-testid="stFileUploader"]:hover { border-color: var(--cyan) !important; }
[data-testid="stFileUploaderDropzoneInstructions"] { color: var(--muted) !important; font-size: 0.8rem !important; }

/* Sidebar section headers */
.sb-section {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--muted);
    margin: 1.2rem 0 0.5rem;
    padding-bottom: 0.3rem;
    border-bottom: 1px solid var(--border);
}

/* Sidebar stat cards */
.sb-stat {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.6rem 0.8rem;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.6rem;
    font-size: 0.8rem;
}
.sb-stat-icon { font-size: 1.1rem; }
.sb-stat-label { color: var(--muted); font-size: 0.72rem; }
.sb-stat-value { color: var(--text); font-weight: 500; }

/* Buttons */
.stButton button {
    font-family: 'Outfit', sans-serif !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
    transition: all 0.2s !important;
}

/* Alerts */
[data-testid="stAlert"] {
    border-radius: 12px !important;
    font-size: 0.82rem !important;
    font-family: 'Outfit', sans-serif !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #ff6b2b33; border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: #ff6b2b66; }

/* Code */
code {
    font-family: 'JetBrains Mono', monospace !important;
    background: #ff6b2b18 !important;
    color: var(--orange) !important;
    padding: 0.1em 0.4em !important;
    border-radius: 5px !important;
    font-size: 0.82em !important;
}
pre {
    background: #09090d !important;
    border-left: 3px solid var(--cyan) !important;
    border-radius: 0 10px 10px 0 !important;
    padding: 1rem !important;
    overflow-x: auto !important;
}
pre code { background: transparent !important; color: #c8d0e8 !important; }

/* Animations */
@keyframes fadeDown  { from{opacity:0;transform:translateY(-14px)} to{opacity:1;transform:none} }
@keyframes fadeUp    { from{opacity:0;transform:translateY(8px)}   to{opacity:1;transform:none} }
@keyframes fadeIn    { from{opacity:0}                             to{opacity:1}                }
@keyframes glowPulse {
    0%,100% { box-shadow: 0 0 24px #ff6b2b55, 0 4px 12px #0008; }
    50%      { box-shadow: 0 0 36px #ff6b2b88, 0 4px 16px #0008; }
}
@keyframes scanline {
    0%   { background-position: 0 0; }
    100% { background-position: 0 100px; }
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

# ── Try loading API key from Streamlit secrets (for cloud deploy) ──
def get_api_key_from_secrets():
    try:
        return st.secrets.get("GOOGLE_API_KEY", "")
    except Exception:
        return ""

# ── Header ────────────────────────────────────────────────────
st.markdown("""
<div class="prism-header">
  <div class="prism-top">
    <div class="prism-icon-wrap">🖨️</div>
    <div class="prism-title-block">
      <div class="prism-title">SENA</div>
      <div class="prism-subtitle">3D Printing Lab Assistant · RAG + Gemini Flash</div>
    </div>
  </div>
  <div class="filament-dots">
    <div class="fdot" style="background:#ff6b2b;color:#ff6b2b"></div>
    <div class="fdot" style="background:#00d4e8;color:#00d4e8"></div>
    <div class="fdot" style="background:#a3e635;color:#a3e635"></div>
    <div class="fdot" style="background:#f472b6;color:#f472b6"></div>
    <div class="fdot" style="background:#a78bfa;color:#a78bfa"></div>
    <span style="font-size:0.65rem;color:#3a4060;font-family:monospace;margin-left:4px">filament palette</span>
  </div>
  <div class="status-row">
    <span class="chip chip-orange"><span class="chip-dot"></span>FDM · SLA · SLS</span>
    <span class="chip chip-cyan"><span class="chip-dot"></span>RAG-powered</span>
    <span class="chip chip-lime"><span class="chip-dot"></span>Gemini 1.5 Flash</span>
    <span class="chip chip-pink"><span class="chip-dot"></span>ChromaDB</span>
  </div>
</div>
<div class="divider-gradient"></div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="font-size:1.2rem;font-weight:700;color:#ff6b2b;font-family:monospace">⬡ SENA</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.7rem;color:#3a4060;font-family:monospace;margin-bottom:1rem">3D Printing Lab Assistant</div>', unsafe_allow_html=True)

    st.markdown('<div class="sb-section">🔑 API Configuration</div>', unsafe_allow_html=True)

    # Auto-load from secrets if available
    secret_key = get_api_key_from_secrets()
    if secret_key:
        st.markdown(
            '<div class="sb-stat"><span class="sb-stat-icon">✅</span><div><div class="sb-stat-label">API Key</div><div class="sb-stat-value">Loaded from secrets</div></div></div>',
            unsafe_allow_html=True,
        )
        api_key = secret_key
    else:
        api_key = st.text_input(
            "Google API Key",
            type="password",
            placeholder="AIza...",
            help="Or set GOOGLE_API_KEY in .streamlit/secrets.toml",
        )
        st.markdown(
            '<a href="https://aistudio.google.com/app/apikey" target="_blank" style="font-size:0.75rem;color:#ff6b2b;text-decoration:none">🔗 Get API key →</a>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="sb-section">📄 Lab Manual</div>', unsafe_allow_html=True)
    uploaded_pdf = st.file_uploader(
        "Upload PDF manual",
        type=["pdf"],
        help="Chunks stored in ChromaDB for semantic search",
        label_visibility="collapsed",
    )

    # Ingest PDF
    if uploaded_pdf and api_key:
        pdf_key = f"pdf_{uploaded_pdf.name}_{uploaded_pdf.size}"
        if pdf_key not in st.session_state:
            prog = st.progress(0, text="⚙️ Extracting text...")
            try:
                pipeline = SENARagPipeline(api_key=api_key)
                prog.progress(30, text="🔢 Chunking...")
                n = pipeline.ingest_pdf(uploaded_pdf.read(), source=uploaded_pdf.name)
                prog.progress(100, text="✅ Done!")
                st.session_state[pdf_key] = n
                st.session_state["pdf_loaded"] = True
                st.session_state["pdf_name"] = uploaded_pdf.name
                st.session_state["pdf_chunks"] = n
                prog.empty()
                st.success(f"✅ Indexed **{n} chunks** from `{uploaded_pdf.name}`")
            except Exception as e:
                prog.empty()
                st.error(f"❌ {e}")
        else:
            n = st.session_state[pdf_key]
            st.markdown(
                f'<div class="sb-stat"><span class="sb-stat-icon">📄</span><div><div class="sb-stat-label">Manual loaded</div><div class="sb-stat-value">{uploaded_pdf.name[:22]}…</div></div></div>',
                unsafe_allow_html=True,
            )
    elif uploaded_pdf and not api_key:
        st.warning("⚠️ Add API key first")

    # DB Status
    st.markdown('<div class="sb-section">🗄️ Database Status</div>', unsafe_allow_html=True)
    if st.session_state.get("pdf_loaded"):
        st.markdown(f"""
        <div class="sb-stat"><span class="sb-stat-icon">🟢</span>
          <div>
            <div class="sb-stat-label">ChromaDB</div>
            <div class="sb-stat-value">{st.session_state.get('pdf_chunks', '?')} vectors indexed</div>
          </div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="sb-stat"><span class="sb-stat-icon">🔴</span>
          <div>
            <div class="sb-stat-label">ChromaDB</div>
            <div class="sb-stat-value">No manual loaded</div>
          </div>
        </div>""", unsafe_allow_html=True)

    msg_count = len([m for m in st.session_state.get("messages", []) if m["role"] == "user"])
    st.markdown(f"""
    <div class="sb-stat"><span class="sb-stat-icon">💬</span>
      <div>
        <div class="sb-stat-label">Session</div>
        <div class="sb-stat-value">{msg_count} messages</div>
      </div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="sb-section">⚡ Actions</div>', unsafe_allow_html=True)
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown(
        '<div style="margin-top:1.5rem;font-size:0.65rem;color:#2a3040;font-family:monospace;text-align:center">SENA v1.0 · Built with ❤️<br>Gemini Flash · ChromaDB · Streamlit</div>',
        unsafe_allow_html=True,
    )

# ── Session state ─────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Render history ────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-icon">🖨️</div>
        <div class="empty-title">SENA is warmed up and ready to print answers</div>
        <div class="suggest-grid">
            <div class="suggest-card">
                <div class="suggest-icon">🛏️</div>
                <div class="suggest-text">How do I level my print bed properly?</div>
            </div>
            <div class="suggest-card">
                <div class="suggest-icon">🌡️</div>
                <div class="suggest-text">Best temperature settings for PETG?</div>
            </div>
            <div class="suggest-card">
                <div class="suggest-icon">🔧</div>
                <div class="suggest-text">Why is my print warping at the corners?</div>
            </div>
            <div class="suggest-card">
                <div class="suggest-icon">🧵</div>
                <div class="suggest-text">Difference between PLA and PLA+?</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and "rag_used" in msg:
                if msg["rag_used"]:
                    pages = msg.get("pages", [])
                    pg = f" · pp. {', '.join(str(p) for p in pages)}" if pages else ""
                    st.markdown(
                        f'<div class="source-badge badge-manual"><span class="badge-dot"></span>📄 Lab manual{pg}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        '<div class="source-badge badge-ai"><span class="badge-dot"></span>🧠 General expertise</div>',
                        unsafe_allow_html=True,
                    )

# ── Chat input ────────────────────────────────────────────────
if prompt := st.chat_input("Ask SENA anything about 3D printing..."):
    if not api_key:
        st.error("🔑 Enter your Google API key in the sidebar to start.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    pipeline = SENARagPipeline(api_key=api_key)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full = ""
        used_rag, pages = False, []
        try:
            stream, used_rag, pages = pipeline.answer(
                query=prompt,
                history=st.session_state.messages[:-1],
                stream=True,
            )
            for chunk in stream:
                full += chunk.text
                placeholder.markdown(full + " ▌")
            placeholder.markdown(full)

            badge_cls = "badge-manual" if used_rag else "badge-ai"
            badge_icon = "📄 Lab manual" if used_rag else "🧠 General expertise"
            pg_str = f" · pp. {', '.join(str(p) for p in pages)}" if pages and used_rag else ""
            st.markdown(
                f'<div class="source-badge {badge_cls}"><span class="badge-dot"></span>{badge_icon}{pg_str}</div>',
                unsafe_allow_html=True,
            )
        except Exception as e:
            full = f"⚠️ Something went wrong: `{e}`"
            placeholder.markdown(full)

    st.session_state.messages.append({
        "role": "assistant",
        "content": full,
        "rag_used": used_rag,
        "pages": pages,
    })
