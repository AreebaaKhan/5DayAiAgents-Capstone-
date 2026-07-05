"""Streamlit UI for the AI Brand Content Strategist.

Premium dark UI with custom niche/topic inputs, LinkedIn post preview
with one-click copy, infographic display, and pipeline details.
"""

import asyncio
import os
import re
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

import streamlit as st

from cli import load_personas
from pipeline import run_pipeline
from utils.model_config import DEFAULT_MODEL
from utils.demo_fallback import run_demo_fallback


# ── Helpers ───────────────────────────────────────────────────────────

@contextmanager
def temporary_env(var_name: str, value: str):
    previous = os.environ.get(var_name)
    if value is None:
        os.environ.pop(var_name, None)
    else:
        os.environ[var_name] = value
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop(var_name, None)
        else:
            os.environ[var_name] = previous


def is_quota_error(msg: str) -> bool:
    m = msg.lower()
    return "resource_exhausted" in m or "429" in m or "quota" in m


def build_model_options() -> list[str]:
    return [DEFAULT_MODEL, "gemini-2.0-flash", "gemini-1.5-flash"]


def extract_post_sections(post_text: str) -> dict:
    sections = {"hook": "", "body": "", "cta": "", "hashtags": ""}
    current = None
    for line in post_text.strip().split("\n"):
        u = line.strip().upper()
        if u.startswith("HOOK:"):
            current = "hook"; rest = line.strip()[5:].strip()
            if rest: sections["hook"] = rest
            continue
        elif u.startswith("BODY:"):
            current = "body"; rest = line.strip()[5:].strip()
            if rest: sections["body"] = rest
            continue
        elif u.startswith("CTA:"):
            current = "cta"; rest = line.strip()[4:].strip()
            if rest: sections["cta"] = rest
            continue
        elif u.startswith("HASHTAGS:"):
            current = "hashtags"; rest = line.strip()[9:].strip()
            if rest: sections["hashtags"] = rest
            continue
        if current and line.strip():
            sections[current] = (sections[current] + "\n" + line.strip()).strip()
    return sections


def get_plain_post_text(s: dict) -> str:
    return "\n\n".join(p for p in [s.get("hook",""), s.get("body",""), s.get("cta",""), s.get("hashtags","")] if p)


# ── Page ──────────────────────────────────────────────────────────────

st.set_page_config(page_title="AI Content Strategist", page_icon="🚀", layout="wide")

# ── CSS ───────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

*, html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

.stApp {
    background: linear-gradient(160deg, #0a0a14 0%, #12121f 35%, #151525 65%, #0e1628 100%);
}

#MainMenu, footer, header {visibility: hidden;}

/* ── Inputs: guaranteed visible text ── */
input, textarea, select, .stTextInput input, .stTextArea textarea,
.stSelectbox [data-baseweb="select"] * {
    color: #f0f0ff !important;
    caret-color: #a78bfa !important;
}
.stTextInput input, .stTextArea textarea {
    background: rgba(30, 30, 50, 0.8) !important;
    border: 1px solid rgba(120, 120, 180, 0.25) !important;
    border-radius: 10px !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #667eea !important;
    box-shadow: 0 0 0 2px rgba(102,126,234,0.2) !important;
}
.stTextInput input::placeholder, .stTextArea textarea::placeholder {
    color: rgba(160, 160, 200, 0.5) !important;
}
label, .stSelectbox label, .stTextInput label, .stTextArea label {
    color: #b0b0d0 !important;
    font-weight: 500 !important;
}

/* ── Selectbox ── */
.stSelectbox [data-baseweb="select"] {
    background: rgba(30, 30, 50, 0.8) !important;
    border: 1px solid rgba(120, 120, 180, 0.25) !important;
    border-radius: 10px !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: rgba(20, 20, 35, 0.6);
    border-radius: 12px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    color: #8888aa !important;
    font-weight: 500;
}
.stTabs [aria-selected="true"] {
    background: rgba(102, 126, 234, 0.2) !important;
    color: #c8c8ff !important;
}

/* ── Hero ── */
.hero {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 45%, #e040fb 100%);
    border-radius: 20px;
    padding: 2.4rem 2.8rem;
    margin-bottom: 1.8rem;
    box-shadow: 0 24px 80px rgba(102,126,234,0.25), 0 0 0 1px rgba(255,255,255,0.08) inset;
    position: relative;
    overflow: hidden;
}
.hero::after {
    content: '';
    position: absolute;
    top: -40%; right: -10%;
    width: 320px; height: 320px;
    background: radial-gradient(circle, rgba(255,255,255,0.12) 0%, transparent 70%);
    border-radius: 50%;
}
.hero-badge {
    display: inline-block;
    background: rgba(255,255,255,0.18);
    padding: 5px 16px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: white;
    margin-bottom: 0.8rem;
    backdrop-filter: blur(8px);
}
.hero h1 { color: white; font-size: 2.1rem; font-weight: 800; margin: 0 0 0.4rem; letter-spacing: -0.3px; }
.hero p  { color: rgba(255,255,255,0.85); font-size: 0.98rem; margin: 0; line-height: 1.6; max-width: 550px; }

/* ── Glass card ── */
.gcard {
    background: rgba(22, 22, 40, 0.7);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(100, 100, 160, 0.15);
    border-radius: 14px;
    padding: 1.4rem;
    margin-bottom: 1rem;
}
.gcard h3 {
    color: #9d8cff;
    font-size: 0.72rem;
    font-weight: 700;
    margin: 0 0 0.8rem;
    text-transform: uppercase;
    letter-spacing: 1.4px;
}

/* ── Status dots ── */
.sr { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; font-size: 0.86rem; }
.d-on  { width: 7px; height: 7px; border-radius: 50%; background: #4ade80; box-shadow: 0 0 8px rgba(74,222,128,0.5); flex-shrink:0; }
.d-off { width: 7px; height: 7px; border-radius: 50%; background: #4b5563; flex-shrink:0; }
.sl { color: #8888aa; }

/* ── LinkedIn card ── */
.lic {
    background: #1d2226;
    border: 1px solid #38434f;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 12px 40px rgba(0,0,0,0.4);
}
.lic-hdr { display: flex; align-items: center; gap: 12px; padding: 16px 18px 10px; }
.lic-av {
    width: 48px; height: 48px; border-radius: 50%;
    background: linear-gradient(135deg, #667eea, #e040fb);
    display: flex; align-items: center; justify-content: center;
    color: white; font-weight: 700; font-size: 1.1rem; flex-shrink:0;
}
.lic-nm { color: #e7e9ea; font-size: 0.95rem; font-weight: 600; margin:0; line-height:1.3; }
.lic-tm { color: #71767b; font-size: 0.78rem; margin:0; }
.lic-bd { padding: 4px 18px 14px; }
.lic-hk { color: #f0f0f5; font-size: 1rem; font-weight: 700; line-height: 1.5; margin-bottom: 12px; }
.lic-tx { color: #c8ccd0; font-size: 0.9rem; line-height: 1.75; white-space: pre-wrap; margin-bottom: 10px; }
.lic-tg { color: #58a6ff; font-size: 0.88rem; font-weight: 500; margin-top: 8px; }
.lic-dv { border-top: 1px solid #2f3336; margin: 0; }
.lic-acts { display: flex; gap: 2px; padding: 2px 8px 6px; }
.lic-act {
    flex: 1; display: flex; align-items: center; justify-content: center;
    gap: 5px; color: #71767b; font-size: 0.8rem; font-weight: 500;
    padding: 8px 4px; border-radius: 6px;
}

/* ── Section title ── */
.stitle { color: #d0d0ff; font-size: 1.15rem; font-weight: 700; margin: 1.5rem 0 0.8rem; }

/* ── Copy button ── */
.copy-wrap {
    display: flex;
    justify-content: flex-end;
    padding: 6px 18px 12px;
    background: #1d2226;
    border-bottom-left-radius: 12px;
    border-bottom-right-radius: 12px;
}

</style>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────

st.markdown("""
<div class="hero">
    <div class="hero-badge">⚡ 5-Agent AI Pipeline</div>
    <h1>LinkedIn Content Strategist</h1>
    <p>Enter any niche and topic — AI agents research live trends, write an engaging post, and generate a branded infographic.</p>
</div>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### ⚙️ Settings")
    selected_model = st.selectbox("Gemini Model", build_model_options(), index=0)
    st.caption("Free-tier quota is limited. Switch models if needed.")
    st.divider()
    st.markdown("### 📡 Status")
    gk = bool(os.environ.get("GOOGLE_API_KEY") and os.environ.get("GOOGLE_API_KEY") != "your-google-api-key-here")
    sk = bool(os.environ.get("SERPER_API_KEY"))
    st.markdown(f"""
    <div class="gcard">
        <div class="sr"><span class="{'d-on' if gk else 'd-off'}"></span><span class="sl">Google API — {'ready ✓' if gk else 'missing'}</span></div>
        <div class="sr"><span class="d-on"></span><span class="sl">Web Search — DuckDuckGo (free)</span></div>
        <div class="sr"><span class="{'d-on' if sk else 'd-off'}"></span><span class="sl">Serper API — {'active' if sk else 'optional'}</span></div>
    </div>
    """, unsafe_allow_html=True)


# ── Input ─────────────────────────────────────────────────────────────

st.markdown('<div class="stitle">🎯 Configure Your Content</div>', unsafe_allow_html=True)

personas = load_personas()

# Two modes: use presets OR go custom — all fields always visible
mode = st.radio(
    "Choose mode",
    ["📝 Enter Custom Niche & Topic", "📂 Use a Preset Persona"],
    horizontal=True,
    label_visibility="collapsed",
)

col_form, col_info = st.columns([1.4, 0.6], gap="large")

with col_form:
    if mode == "📝 Enter Custom Niche & Topic":
        r1a, r1b = st.columns(2)
        with r1a:
            custom_niche = st.text_input("🏷️ Your Niche *", placeholder="e.g. AI Agents, Real Estate, Fitness")
        with r1b:
            custom_tone = st.selectbox("🎤 Tone", [
                "Professional & insightful",
                "Conversational & friendly",
                "Bold & opinionated",
                "Vulnerable & authentic",
                "Educational & data-driven",
            ])

        custom_topic = st.text_input(
            "📝 Target Topic (leave blank for AI to choose)",
            placeholder="e.g. How to use AI agents for lead generation",
        )

        r2a, r2b = st.columns(2)
        with r2a:
            custom_audience = st.text_input("👥 Target Audience", placeholder="e.g. Tech founders, Students")
        with r2b:
            custom_goal = st.text_input("🎯 Posting Goal", value="Build thought leadership")

    else:
        persona_labels = [f"{p['data']['name']} — {p['data']['niche']}" for p in personas]
        selected_idx = st.selectbox("Select persona", range(len(persona_labels)), format_func=lambda i: persona_labels[i])
        preset_data = personas[selected_idx]["data"]
        custom_niche    = preset_data.get("niche", "")
        custom_tone     = preset_data.get("tone", "Professional")
        custom_audience = preset_data.get("audience", "")
        custom_goal     = preset_data.get("posting_goal", "")

        st.success(f"**{preset_data['name']}** — {preset_data['niche']}")

        custom_topic = st.text_input(
            "📝 Override Topic (optional)",
            placeholder="Leave blank to let AI choose a topic",
        )

with col_info:
    st.markdown("""
    <div class="gcard">
        <h3>How It Works</h3>
        <p style="color:#9ca3af; font-size:0.85rem; line-height:1.8; margin:0;">
            <strong style="color:#a78bfa;">1.</strong> Planner picks the best angle<br>
            <strong style="color:#a78bfa;">2.</strong> Researcher searches live web<br>
            <strong style="color:#a78bfa;">3.</strong> Writer crafts your post<br>
            <strong style="color:#a78bfa;">4.</strong> Visual creates an infographic<br>
            <strong style="color:#a78bfa;">5.</strong> Publisher reviews output
        </p>
    </div>
    """, unsafe_allow_html=True)


# ── Run ───────────────────────────────────────────────────────────────

st.markdown("---")
can_run = bool(custom_niche.strip())
if not can_run and mode == "📝 Enter Custom Niche & Topic":
    st.warning("Enter a niche to get started.")

run_clicked = st.button("🚀  Generate Content + Infographic", type="primary", use_container_width=True, disabled=not can_run)

if run_clicked:
    if mode == "📝 Enter Custom Niche & Topic":
        active_persona = {
            "name": custom_niche.strip().title() + " Creator",
            "niche": custom_niche.strip(),
            "tone": custom_tone,
            "audience": custom_audience.strip() or "Professionals",
            "posting_goal": custom_goal.strip() or "Build thought leadership",
            "posting_frequency": "Daily",
            "example_topics": [custom_topic.strip()] if custom_topic.strip() else [],
            "target_topic": custom_topic.strip(),
        }
    else:
        active_persona = dict(preset_data)
        if custom_topic.strip():
            active_persona["target_topic"] = custom_topic.strip()

    with st.spinner(f"Running 5-agent pipeline for **{active_persona['name']}**…"):
        try:
            with temporary_env("CONTENT_PIPELINE_APPROVAL_MODE", "auto"):
                with temporary_env("CONTENT_PIPELINE_MODEL", selected_model):
                    results = asyncio.run(run_pipeline(active_persona))
            st.session_state["latest_results"] = results
            st.session_state["active_persona"] = active_persona
            st.session_state.pop("pipeline_error", None)
            st.session_state.pop("fallback_notice", None)
        except Exception as exc:
            err = str(exc)
            if is_quota_error(err):
                fid = datetime.now().strftime("%Y%m%d_%H%M%S")
                fb = run_demo_fallback(active_persona, fid)
                st.session_state["latest_results"] = fb
                st.session_state["active_persona"] = active_persona
                st.session_state["fallback_notice"] = True
                st.session_state.pop("pipeline_error", None)
            else:
                st.session_state["pipeline_error"] = err
                st.session_state.pop("latest_results", None)


# ── Display ───────────────────────────────────────────────────────────

results        = st.session_state.get("latest_results")
pipeline_error = st.session_state.get("pipeline_error")
fallback       = st.session_state.get("fallback_notice")

if fallback:
    st.warning("⚡ **Gemini quota hit** — used DuckDuckGo live search + dynamic templates. Content is still based on real web data!")

if pipeline_error:
    st.error("Pipeline error. Try switching the model in the sidebar.")
    with st.expander("Details"):
        st.code(str(pipeline_error))

if results:
    ar = results.get("results", {})
    pname = results.get("persona", "Creator")
    initials = "".join(w[0].upper() for w in pname.split()[:2])
    rid = results.get("run_id", "—")

    # Locate infographic
    img_raw = ar.get("visual_agent", "")
    img_str = str(img_raw) if img_raw else ""
    if "image_path" in img_str:
        m = re.search(r'assets[/\\][^\s"\']+\.png', img_str)
        if m:
            img_str = m.group(0)
    has_img = bool(img_str and Path(img_str).exists())

    post_text = str(ar.get("writer_agent", ""))
    sec = extract_post_sections(post_text)
    plain = get_plain_post_text(sec)

    st.markdown('<div class="stitle">📋 Results</div>', unsafe_allow_html=True)

    # ── Two columns: Post + Infographic ───────────────────────────
    lcol, rcol = st.columns([1.05, 0.95], gap="large")

    with lcol:
        st.markdown("##### 📱 LinkedIn Post Preview")

        hook_e = sec.get("hook","").replace("<","&lt;").replace(">","&gt;")
        body_e = sec.get("body","").replace("<","&lt;").replace(">","&gt;").replace("\n","<br>")
        cta_e  = sec.get("cta","").replace("<","&lt;").replace(">","&gt;")
        tags_e = sec.get("hashtags","").replace("<","&lt;").replace(">","&gt;")

        st.markdown(f"""
        <div class="lic">
            <div class="lic-hdr">
                <div class="lic-av">{initials}</div>
                <div><p class="lic-nm">{pname}</p><p class="lic-tm">Just now · 🌐</p></div>
            </div>
            <div class="lic-bd">
                <div class="lic-hk">{hook_e}</div>
                <div class="lic-tx">{body_e}</div>
                <div class="lic-tx">{cta_e}</div>
                <div class="lic-tg">{tags_e}</div>
            </div>
            <hr class="lic-dv">
            <div class="lic-acts">
                <div class="lic-act">👍 Like</div>
                <div class="lic-act">💬 Comment</div>
                <div class="lic-act">🔄 Repost</div>
                <div class="lic-act">📤 Send</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Copy button using st.code (selectable) instead of text_area
        st.markdown("")
        st.code(plain, language=None)
        st.caption("☝️ Click inside the box above and press Ctrl+A → Ctrl+C to copy the full post.")

    with rcol:
        # ── INFOGRAPHIC — prominent ──────────────────────────────
        st.markdown("##### 🖼️ Generated Infographic")

        if has_img:
            st.image(img_str, caption="Save this image and attach it when posting on LinkedIn", use_container_width=True)
            st.success(f"Saved: `{img_str}`")
        else:
            st.warning("Infographic was not generated. Check Visual tab below.")
            if img_raw:
                st.caption(f"Agent output: {str(img_raw)[:200]}")

        st.markdown("---")

        # ── Details tabs ─────────────────────────────────────────
        st.markdown("##### 📊 Details")
        t1, t2, t3 = st.tabs(["Topic Plan", "Research", "Status"])

        with t1:
            planned = str(ar.get("planner_agent", "—"))
            st.markdown(f"""<div class="gcard"><h3>Planned Topic</h3>
            <p style="color:#c8c8d0; font-size:0.88rem; line-height:1.65; white-space:pre-wrap; margin:0;">{planned[:900]}</p>
            </div>""", unsafe_allow_html=True)

        with t2:
            research = str(ar.get("research_agent", "—"))
            if len(research) > 1800:
                research = research[:1800] + "\n…"
            st.code(research, language="text")

        with t3:
            st.markdown(f"""<div class="gcard"><h3>Run Info</h3>
            <div class="sr"><span class="d-on"></span><span class="sl">Run: {rid}</span></div>
            <div class="sr"><span class="d-on"></span><span class="sl">Persona: {pname}</span></div>
            <div class="sr"><span class="d-on"></span><span class="sl">Model: {selected_model}</span></div>
            <div class="sr"><span class="d-on"></span><span class="sl">Saved: outputs/{rid}/</span></div>
            </div>""", unsafe_allow_html=True)


# ── Empty state ───────────────────────────────────────────────────────

if not results and not pipeline_error:
    st.markdown("""
    <div class="gcard" style="text-align:center; padding:3rem 2rem; margin-top:1rem;">
        <div style="font-size:3rem; margin-bottom:0.8rem;">🚀</div>
        <h3 style="color:#d0d0ff; font-size:1.15rem; margin:0 0 0.5rem;">Ready to create content</h3>
        <p style="color:#6b7280; margin:0; font-size:0.92rem; line-height:1.6;">
            Enter your niche, click <strong style="color:#a78bfa;">Generate Content + Infographic</strong>,
            and get a LinkedIn post preview + branded visual — ready to copy and post.
        </p>
    </div>
    """, unsafe_allow_html=True)
