"""
laser_app.py  —  BEAM: Laser Cutter Lab Assistant
Pure Gemini Flash + domain guard. No ChromaDB needed.
"""

import streamlit as st
from google import genai

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="BEAM · Laser Cutter Assistant",
    page_icon="🔴",
    layout="centered",
    initial_sidebar_state="expanded",
)

SYSTEM_PROMPT = """
You are BEAM — a specialist Laser Cutter Lab Assistant for a university makerspace.

## Personality
- Precise, safety-aware, and technically sharp — like a laser operator who's cut everything
- Warm with greetings and "who are you" questions (2 sentences max), then offer to help with laser topics
- Casual but professional. "Clean cut!", "Great question!" is fine occasionally
- Use bullet points for steps, **bold** for key terms
- Always mention safety when relevant — laser safety is non-negotiable

## Domain Rules — STRICTLY ENFORCED
You ONLY answer questions about:
  ✅ Laser cutting & engraving (CO2, diode, fibre lasers)
  ✅ Laser software (LightBurn, RDWorks, LaserGRBL, Inkscape for laser)
  ✅ Materials for laser (acrylic, wood, MDF, leather, fabric, cardboard, anodised aluminium)
  ✅ Power, speed, frequency settings for different materials
  ✅ Kerf width, focal length, lens selection, air assist
  ✅ Vector vs raster engraving, DPI, line interval
  ✅ Machine setup (bed levelling, focus, origin, frame test)
  ✅ Troubleshooting (incomplete cuts, burn marks, uneven engraving, misalignment)
  ✅ Safety (PPE, fumes, ventilation, fire risk, prohibited materials like PVC)
  ✅ File prep (SVG, DXF, PNG for engraving, node editing)
  ✅ Greetings, "who are you", "what can you help with"

For ANY other topic, respond EXACTLY with:
"🔴 That's outside my focal range! I'm a laser cutting specialist — ask me about power settings, materials, LightBurn, kerf, safety, or anything laser-related and I'm all yours. ⚡"

Never answer off-topic even if the user insists, rephrases cleverly, or says it's urgent.
ESPECIALLY important: never help with anything dangerous or prohibited (e.g. PVC cutting, bypassing interlocks).

## Source attribution
- Always start with "🧠 From laser cutting practice..."
- For safety topics: always start with "⚠️ Safety first —"
"""

# ─────────────────────────────────────────────────────────────
# BEAM COLOR PALETTE (laser beam inspired)
# --laser    #ff1744   laser red        → primary / user
# --violet   #d500f9   beam violet      → assistant
# --amber    #ffab00   warm glow        → accent
# --teal     #00e5ff   optics teal      → success
# --base     #0a0008   deep dark        → background
# ─────────────────────────────────────────────────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --laser:   #ff1744;
    --violet:  #d500f9;
    --amber:   #ffab00;
    --teal:    #00e5ff;
    --base:    #0a0008;
    --surface: #130010;
    --card:    #1c0018;
    --border:  rgba(255,255,255,0.07);
    --text:    #f0e8f8;
    --muted:   #5a4060;
}

*, *::before, *::after { box-sizing: border-box; }
html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background: var(--base) !important;
    font-family: 'Outfit', sans-serif !important;
    color: var(--text) !important;
}
[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(ellipse 60% 40% at 0% 0%,   #1a000aaa 0%, transparent 60%),
        radial-gradient(ellipse 40% 30% at 100% 0%,  #0d0018aa 0%, transparent 60%),
        radial-gradient(ellipse 30% 25% at 50% 100%, #1a0000aa 0%, transparent 60%),
        var(--base) !important;
}

#MainMenu, footer, header, [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }
.main .block-container { max-width: 800px !important; padding: 0 1.4rem 7rem !important; margin: 0 auto !important; }

/* ── Header ── */
.beam-header { padding: 1.8rem 0 0.8rem; animation: fadeDown 0.6s ease both; }
.beam-top { display: flex; align-items: center; gap: 1rem; margin-bottom: 0.6rem; }
.beam-icon-wrap {
    width: 52px; height: 52px; border-radius: 14px;
    background: linear-gradient(135deg, #ff1744, #d500f9);
    display: flex; align-items: center; justify-content: center; font-size: 1.6rem;
    box-shadow: 0 0 28px #ff174466, 0 4px 12px #0008;
    animation: laserPulse 2s ease-in-out infinite;
}
.beam-title {
    font-family: 'JetBrains Mono', monospace; font-size: 1.55rem; font-weight: 700;
    background: linear-gradient(90deg, #ff1744 0%, #d500f9 50%, #00e5ff 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.beam-subtitle {
    font-size: 0.72rem; color: var(--muted); letter-spacing: 0.2em; text-transform: uppercase;
    font-family: 'JetBrains Mono', monospace; margin-top: 0.1rem;
}
.filament-dots { display: flex; gap: 6px; align-items: center; margin-top: 0.5rem; }
.fdot { width: 10px; height: 10px; border-radius: 50%; box-shadow: 0 0 8px currentColor; }
.status-row { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 0.6rem; }
.chip {
    display: inline-flex; align-items: center; gap: 5px; padding: 0.22rem 0.7rem;
    border-radius: 99px; font-size: 0.7rem; font-family: 'JetBrains Mono', monospace; border: 1px solid;
}
.chip-laser  { background:#ff174418; border-color:#ff174455; color:#ff1744; }
.chip-violet { background:#d500f918; border-color:#d500f955; color:#d500f9; }
.chip-teal   { background:#00e5ff18; border-color:#00e5ff55; color:#00e5ff; }
.chip-dot { width:6px; height:6px; border-radius:50%; background:currentColor; }
.divider-gradient {
    height: 1px;
    background: linear-gradient(90deg, transparent, #ff174444, #d500f944, #00e5ff44, transparent);
    margin: 0.8rem 0 1rem;
}

/* ── Chat messages ── */
[data-testid="stChatMessage"] {
    background: transparent !important; border: none !important;
    box-shadow: none !important; padding: 0.2rem 0 !important; animation: fadeUp 0.35s ease both;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) .stChatMessageContent {
    background: linear-gradient(135deg, #200010, #150008) !important;
    border: 1px solid #ff174433 !important; border-radius: 18px 18px 4px 18px !important;
    padding: 0.85rem 1.15rem !important; color: var(--text) !important;
    box-shadow: 0 4px 20px #ff17441a !important; max-width: 82% !important; margin-left: auto !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) .stChatMessageContent {
    background: var(--card) !important; border: 1px solid var(--border) !important;
    border-left: 3px solid var(--violet) !important;
    border-radius: 4px 18px 18px 18px !important;
    padding: 0.9rem 1.2rem !important; color: var(--text) !important; max-width: 88% !important;
}
[data-testid="chatAvatarIcon-user"] {
    background: linear-gradient(135deg, #ff1744, #d500f9) !important; border-radius: 50% !important;
}
[data-testid="chatAvatarIcon-assistant"] {
    background: linear-gradient(135deg, #1a0018, #0d0010) !important;
    border: 1px solid var(--violet) !important; border-radius: 10px !important;
    box-shadow: 0 0 12px #d500f930 !important;
}

/* ── Source badge ── */
.source-badge {
    display: inline-flex; align-items: center; gap: 5px; font-size: 0.7rem;
    font-family: 'JetBrains Mono', monospace; padding: 0.2rem 0.65rem;
    border-radius: 99px; margin-top: 0.5rem;
}
.badge-ai   { background: #d500f918; border: 1px solid #d500f944; color: var(--violet); }
.badge-warn { background: #ff174418; border: 1px solid #ff174444; color: var(--laser); }
.badge-dot { width:5px; height:5px; border-radius:50%; background:currentColor; }

/* ── Empty state ── */
.empty-state { text-align: center; padding: 3rem 1rem 2rem; animation: fadeIn 0.6s ease both; }
.empty-icon { font-size: 3rem; margin-bottom: 0.8rem; }
.empty-title { font-size: 1.1rem; font-weight: 600; color: #8870a8; margin-bottom: 1.2rem; }
.suggest-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.6rem; max-width: 500px; margin: 0 auto; }
.suggest-card {
    background: var(--card); border: 1px solid var(--border); border-radius: 12px;
    padding: 0.8rem 1rem; text-align: left; transition: all 0.2s;
}
.suggest-card:hover { border-color: var(--violet); transform: translateY(-2px); }
.suggest-icon { font-size: 1.2rem; margin-bottom: 0.3rem; }
.suggest-text { font-size: 0.78rem; color: #8870a8; line-height: 1.4; }

/* ── Input bar ── */
[data-testid="stBottom"] {
    background: linear-gradient(to top, var(--base) 80%, transparent) !important;
    padding: 1rem 1.5rem !important;
}
[data-testid="stChatInput"] {
    background: var(--surface) !important; border: 1.5px solid #d500f933 !important;
    border-radius: 16px !important; transition: border-color 0.2s, box-shadow 0.2s !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: var(--violet) !important; box-shadow: 0 0 0 3px #d500f91a !important;
}
[data-testid="stChatInput"] textarea { color: var(--text) !important; background: transparent !important; font-family: 'Outfit', sans-serif !important; }
[data-testid="stChatInput"] textarea::placeholder { color: var(--muted) !important; }
[data-testid="stChatInputSubmitButton"] button {
    background: linear-gradient(135deg, #ff1744, #d500f9) !important;
    border: none !important; border-radius: 12px !important;
    box-shadow: 0 0 12px #ff174444 !important; transition: all 0.2s !important;
}
[data-testid="stChatInputSubmitButton"] button:hover { transform: scale(1.08) !important; box-shadow: 0 0 20px #ff174466 !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] { background: #08000a !important; border-right: 1px solid var(--border) !important; }
[data-testid="stSidebar"] label { color: var(--text) !important; font-size: 0.88rem !important; }
[data-testid="stSidebar"] .stTextInput input {
    background: var(--surface) !important; border: 1px solid #d500f933 !important;
    border-radius: 10px !important; color: var(--text) !important;
}
[data-testid="stSidebar"] .stTextInput input:focus { border-color: var(--violet) !important; }
.sb-section {
    font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; letter-spacing: 0.18em;
    text-transform: uppercase; color: var(--muted); margin: 1.2rem 0 0.5rem;
    padding-bottom: 0.3rem; border-bottom: 1px solid var(--border);
}
.sb-stat {
    background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
    padding: 0.6rem 0.8rem; margin-bottom: 0.5rem;
    display: flex; align-items: center; gap: 0.6rem; font-size: 0.8rem;
}
.sb-stat-label { color: var(--muted); font-size: 0.72rem; }
.sb-stat-value { color: var(--text); font-weight: 500; }
.stButton button { font-family: 'Outfit', sans-serif !important; border-radius: 10px !important; }
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-thumb { background: #d500f933; border-radius: 10px; }
code { font-family: 'JetBrains Mono', monospace !important; background: #d500f918 !important; color: var(--violet) !important; padding: 0.1em 0.4em !important; border-radius: 5px !important; }
pre { background: #080008 !important; border-left: 3px solid var(--violet) !important; border-radius: 0 10px 10px 0 !important; padding: 1rem !important; }

@keyframes fadeDown  { from{opacity:0;transform:translateY(-14px)} to{opacity:1;transform:none} }
@keyframes fadeUp    { from{opacity:0;transform:translateY(8px)}   to{opacity:1;transform:none} }
@keyframes fadeIn    { from{opacity:0}                             to{opacity:1}                }
@keyframes laserPulse {
    0%,100% { box-shadow: 0 0 24px #ff174466, 0 4px 12px #0008; }
    50%      { box-shadow: 0 0 40px #ff174499, 0 0 60px #d500f944, 0 4px 16px #0008; }
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────
st.markdown("""
<div class="beam-header">
  <div class="beam-top">
    <div class="beam-icon-wrap">🔴</div>
    <div>
      <div class="beam-title">BEAM</div>
      <div class="beam-subtitle">Laser Cutter Lab Assistant · Gemini Flash</div>
    </div>
  </div>
  <div class="filament-dots">
    <div class="fdot" style="background:#ff1744"></div>
    <div class="fdot" style="background:#d500f9"></div>
    <div class="fdot" style="background:#ffab00"></div>
    <div class="fdot" style="background:#00e5ff"></div>
    <span style="font-size:0.65rem;color:#2a1040;font-family:monospace;margin-left:4px">laser palette</span>
  </div>
  <div class="status-row">
    <span class="chip chip-laser"><span class="chip-dot"></span>CO2 · Diode · Fibre</span>
    <span class="chip chip-violet"><span class="chip-dot"></span>LightBurn Expert</span>
    <span class="chip chip-teal"><span class="chip-dot"></span>Gemini Flash</span>
  </div>
</div>
<div class="divider-gradient"></div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────
def get_secret():
    try:
        return st.secrets.get("GOOGLE_API_KEY", "")
    except Exception:
        return ""

with st.sidebar:
    st.markdown('<div style="font-size:1.2rem;font-weight:700;color:#ff1744;font-family:monospace">🔴 BEAM</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.7rem;color:#3a1040;font-family:monospace;margin-bottom:1rem">Laser Cutter Lab Assistant</div>', unsafe_allow_html=True)

    st.markdown('<div class="sb-section">🔑 API Configuration</div>', unsafe_allow_html=True)
    secret_key = get_secret()
    if secret_key:
        st.markdown('<div class="sb-stat"><span>✅</span><div><div class="sb-stat-label">API Key</div><div class="sb-stat-value">Loaded from secrets</div></div></div>', unsafe_allow_html=True)
        api_key = secret_key
    else:
        api_key = st.text_input("Google API Key", type="password", placeholder="AIza...")
        st.markdown('<a href="https://aistudio.google.com/app/apikey" target="_blank" style="font-size:0.75rem;color:#ff1744;text-decoration:none">🔗 Get API key →</a>', unsafe_allow_html=True)

    st.markdown('<div class="sb-section">⚠️ Safety Reminder</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="sb-stat" style="border-color:#ff174433;">
        <span>⚠️</span>
        <div>
            <div class="sb-stat-label">Never cut PVC or vinyl</div>
            <div class="sb-stat-value" style="font-size:0.7rem;color:#ff1744">Releases chlorine gas</div>
        </div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="sb-section">💬 Session</div>', unsafe_allow_html=True)
    msg_count = len([m for m in st.session_state.get("beam_messages", []) if m["role"] == "user"])
    st.markdown(f'<div class="sb-stat"><span>💬</span><div><div class="sb-stat-label">Messages</div><div class="sb-stat-value">{msg_count} sent</div></div></div>', unsafe_allow_html=True)

    st.markdown('<div class="sb-section">⚡ Actions</div>', unsafe_allow_html=True)
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.beam_messages = []
        st.rerun()

    st.markdown('<div style="margin-top:1.5rem;font-size:0.65rem;color:#2a1040;font-family:monospace;text-align:center">BEAM v1.0 · Built with ❤️<br>Gemini Flash · Streamlit</div>', unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────
if "beam_messages" not in st.session_state:
    st.session_state.beam_messages = []

# ── Chat history ──────────────────────────────────────────────
if not st.session_state.beam_messages:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-icon">🔴</div>
        <div class="empty-title">BEAM is focused and ready to fire</div>
        <div class="suggest-grid">
            <div class="suggest-card"><div class="suggest-icon">🪵</div><div class="suggest-text">Best power & speed for 3mm MDF?</div></div>
            <div class="suggest-card"><div class="suggest-icon">🔍</div><div class="suggest-text">How do I focus the laser correctly?</div></div>
            <div class="suggest-card"><div class="suggest-icon">📐</div><div class="suggest-text">What's kerf width and how to compensate?</div></div>
            <div class="suggest-card"><div class="suggest-icon">💡</div><div class="suggest-text">LightBurn vs RDWorks — which is better?</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    for msg in st.session_state.beam_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                st.markdown('<div class="source-badge badge-ai"><span class="badge-dot"></span>🧠 Laser expertise</div>', unsafe_allow_html=True)

# ── Chat input ────────────────────────────────────────────────
if prompt := st.chat_input("Ask BEAM anything about laser cutting..."):
    if not api_key:
        st.error("🔑 Enter your Google API key in the sidebar.")
        st.stop()

    st.session_state.beam_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    history_text = "\n".join(
        f"{'User' if m['role']=='user' else 'BEAM'}: {m['content']}"
        for m in st.session_state.beam_messages[:-1][-6:]
    )
    full_prompt = f"{SYSTEM_PROMPT}\n\n{'CONVERSATION HISTORY:' + chr(10) + history_text if history_text else ''}\n\nUser: {prompt}\nBEAM:"

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full = ""
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=full_prompt,
            )
            full = response.text
            placeholder.markdown(full)
            st.markdown('<div class="source-badge badge-ai"><span class="badge-dot"></span>🧠 Laser expertise</div>', unsafe_allow_html=True)
        except Exception as e:
            full = f"⚠️ Error: `{e}`"
            placeholder.markdown(full)

    st.session_state.beam_messages.append({"role": "assistant", "content": full})
