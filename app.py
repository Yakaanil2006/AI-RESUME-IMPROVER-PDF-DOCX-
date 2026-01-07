import streamlit as st
import fitz  # PyMuPDF
from docx import Document
import google.generativeai as genai
import os
import re

# ------------------ CONFIG ------------------
API_KEY = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

st.set_page_config(
    page_title="ResumeLens",
    page_icon="🚀",
    layout="wide"
)

# ------------------ GLASS + LOGO CSS ------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap');

@keyframes glow {
  0% { text-shadow: 0 0 10px rgba(99,102,241,0.4); }
  50% { text-shadow: 0 0 25px rgba(168,85,247,0.6); }
  100% { text-shadow: 0 0 10px rgba(99,102,241,0.4); }
}

.stApp {
    background-color: #0f172a;
    background-image:
        radial-gradient(at 0% 0%, rgba(99,102,241,0.15), transparent 50%),
        radial-gradient(at 100% 0%, rgba(168,85,247,0.15), transparent 50%),
        radial-gradient(at 100% 100%, rgba(236,72,153,0.1), transparent 50%),
        radial-gradient(at 0% 100%, rgba(45,212,191,0.1), transparent 50%);
    font-family: 'Plus Jakarta Sans', sans-serif;
    color: #f1f5f9;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(255,255,255,0.03);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 24px;
    padding: 2rem;
    box-shadow: 0 8px 32px rgba(0,0,0,0.35);
}

.logo-wrap { text-align: center; }
.logo-text {
    font-size: 3.8rem;
    font-weight: 800;
    letter-spacing: -1.5px;
    background: linear-gradient(90deg, #ffffff, #c7d2fe, #818cf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: glow 4s ease-in-out infinite;
}
.logo-subtitle {
    text-align: center;
    font-size: 0.85rem;
    letter-spacing: 3px;
    font-weight: 600;
    color: #94a3b8;
    margin-bottom: 3rem;
}

.glass-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 20px;
    padding: 25px;
    text-align: center;
    margin-bottom: 20px;
}

.score-text { font-size: 4.5rem; font-weight: 800; }

.stButton > button {
    background: rgba(99,102,241,0.25);
    border: 1px solid rgba(255,255,255,0.25);
    color: white;
    border-radius: 12px;
    padding: 0.6rem 2rem;
    font-weight: 600;
}
.stButton > button:hover {
    background: rgba(99,102,241,0.45);
    transform: translateY(-2px);
}

.stTextArea textarea {
    background: rgba(0,0,0,0.25);
    border: 1px solid rgba(255,255,255,0.15);
    color: white;
}
</style>
""", unsafe_allow_html=True)

# ------------------ HELPERS ------------------
def extract_text_from_pdf(uploaded_file):
    try:
        text = ""
        with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
        return text
    except Exception as e:
        st.error(f"PDF Error: {e}")
        return None

def extract_text_from_docx(uploaded_file):
    try:
        doc = Document(uploaded_file)
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception as e:
        st.error(f"DOCX Error: {e}")
        return None

def extract_text(uploaded_file, resume_type):
    if resume_type == "PDF":
        return extract_text_from_pdf(uploaded_file)
    elif resume_type == "DOCX":
        return extract_text_from_docx(uploaded_file)
    return None

def get_ai_analysis(resume_text, job_desc):
    model = genai.GenerativeModel("gemma-3-27b-it")
    prompt = f"""
Act as a recruiter. Analyze resume vs job description.

FORMAT STRICTLY:
MATCH_SCORE: [0-100]
---
### 💎 Executive Summary
Concise recruiter verdict.

### 🔥 Missing Critical Keywords
JD keywords absent in resume.

### 🛠️ Recommended Actions
Clear ATS optimization steps.

Resume:
{resume_text}

Job Description:
{job_desc}
"""
    return model.generate_content(prompt).text

# ------------------ HEADER ------------------
st.markdown("""
<div class="logo-wrap">
    <span class="logo-text">ResumeLens</span>
</div>
<div class="logo-subtitle">SEE YOUR RESUME THROUGH A RECRUITER’S LENS</div>
""", unsafe_allow_html=True)

# ------------------ LAYOUT ------------------
left, right = st.columns([1, 1.2], gap="large")

with left:
    st.markdown("### 📥 Source Files")

    resume_type = st.radio(
        "Select Resume Format",
        ["PDF", "DOCX"],
        horizontal=True
    )

    resume_file = st.file_uploader(
        f"Upload Resume ({resume_type})",
        type=["pdf"] if resume_type == "PDF" else ["docx"]
    )

    job_text = st.text_area(
        "Job Description",
        height=260,
        placeholder="Paste job requirements..."
    )

    analyze = st.button("Generate AI Audit", use_container_width=True)

    if analyze and (not resume_file or not job_text.strip()):
        st.toast("📄 Please upload resume and job description", icon="⚠️")

with right:
    if analyze and resume_file and job_text.strip():
        with st.spinner("Refining insights..."):
            resume_text = extract_text(resume_file, resume_type)

            if resume_text:
                report = get_ai_analysis(resume_text, job_text)

                score_match = re.search(r"MATCH_SCORE:\s*(\d+)", report)
                score = int(score_match.group(1)) if score_match else 0

                clean_report = re.sub(r"MATCH_SCORE:\s*\d+", "", report).replace("---", "").strip()
                color = "#22c55e" if score > 75 else "#f59e0b" if score > 50 else "#ef4444"

                st.markdown(f"""
                <div class="glass-card">
                    <div style="color:#94a3b8;font-size:0.85rem;">MATCH ACCURACY</div>
                    <div class="score-text" style="color:{color};">{score}%</div>
                    <div style="width:100%;height:12px;background:rgba(255,255,255,0.08);border-radius:20px;">
                        <div style="width:{score}%;height:100%;background:{color};border-radius:20px;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(clean_report)

                txt_content = f"ResumeLens Analysis Report\nMatch Score: {score}%\n\n"
                txt_content += clean_report.replace("### ", "")

                st.download_button(
                    "Download Report (.txt)",
                    txt_content,
                    "ResumeLens_Report.txt",
                    "text/plain",
                    use_container_width=True
                )
    else:
        st.markdown("""
        <div style="border:1px dashed rgba(255,255,255,0.2);
        border-radius:24px;padding:5rem 2rem;text-align:center;">
            <div style="font-size:3rem;">💎</div>
            <h4 style="color:#64748b;">Ready to Analyze</h4>
            <p style="color:#475569;">Upload resume and job description</p>
        </div>
        """, unsafe_allow_html=True)

# ------------------ FOOTER ------------------
st.markdown(
    "<div style='text-align:center;padding:2rem;color:#475569;font-size:1.5rem;'>ResumeLens by Team Ignite • 2026</div>",
    unsafe_allow_html=True
)
