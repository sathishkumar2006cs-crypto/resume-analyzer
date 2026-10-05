import streamlit as st
import pdfplumber
import google.generativeai as genai
import json

# Page Configuration
st.set_page_config(
    page_title="Smart Resume Analyzer & ATS Score",
    page_icon="📄",
    layout="wide"
)

# Custom Styling (Gemini Dark Theme inspired)
st.markdown("""
    <style>
    .stApp {
        background-color: #0d1117;
        color: #f3f4f6;
    }
    .main-card {
        background-color: #161b22;
        padding: 1.5rem;
        border-radius: 16px;
        border: 1px solid #30363d;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📄 AI Resume Analyzer & Job Fit Assistant")
st.caption("Upload your resume and target job description to get an instant ATS match score and feedback.")

# Sidebar for API Key
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Enter Gemini API Key", type="password")
    st.markdown("[Get a free Gemini API Key here](https://aistudio.google.com/)")

# Layout Columns
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Upload Resume")
    uploaded_file = st.file_uploader("Upload PDF Resume", type=["pdf"])

with col2:
    st.subheader("2. Job Description")
    job_description = st.text_area("Paste Target Job Description", height=200, placeholder="Paste job requirements, skills, and duties here...")

# PDF Text Extraction Function
def extract_pdf_text(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

# Analyze Button
if st.button("🚀 Analyze Resume Fit", type="primary", use_container_width=True):
    if not api_key:
        st.error("Please enter your Gemini API Key in the sidebar.")
    elif not uploaded_file:
        st.warning("Please upload a PDF resume.")
    elif not job_description.strip():
        st.warning("Please paste a job description.")
    else:
        with st.spinner("Extracting text and analyzing with Gemini AI..."):
            try:
                # Extract text
                resume_text = extract_pdf_text(uploaded_file)
                
                # Configure Gemini
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-1.5-flash")

                prompt = f"""
                You are an expert ATS (Applicant Tracking System) scanner and technical recruiter.
                Analyze the following resume against the job description.

                RESUME TEXT:
                {resume_text}

                JOB DESCRIPTION:
                {job_description}

                Provide a detailed evaluation structured in JSON format with these exact keys:
                - "match_score": integer between 0 and 100
                - "matched_skills": list of strings (skills found in both)
                - "missing_skills": list of strings (key skills required by job but missing in resume)
                - "rewrites": list of objects with "original" (weak bullet point) and "improved" (ATS optimized version)
                - "interview_questions": list of 3 tailored technical/behavioral interview questions

                Return ONLY valid JSON without markdown wrapping.
                """

                response = model.generate_content(prompt)
                
                # Parse JSON output
                clean_json = response.text.strip().replace("```json", "").replace("```", "")
                data = json.loads(clean_json)

                # Render Results
                st.success("Analysis Complete!")
                st.markdown("---")

                # Score Display
                score = data.get("match_score", 0)
                st.metric("ATS Match Score", f"{score}%")
                st.progress(score / 100)

                # Skills Comparison
                c1, c2 = st.columns(2)
                with c1:
                    st.subheader("✅ Matched Skills")
                    for skill in data.get("matched_skills", []):
                        st.markdown(f"- **{skill}**")

                with c2:
                    st.subheader("⚠️ Missing / Gap Skills")
                    for skill in data.get("missing_skills", []):
                        st.markdown(f"- 🔴 {skill}")

                # Bullet Point Improvements
                st.subheader("💡 Suggested Resume Bullet Improvements")
                for item in data.get("rewrites", []):
                    st.warning(f"**Original:** {item.get('original')}")
                    st.success(f"**ATS Rewritten:** {item.get('improved')}")

                # Interview Questions
                st.subheader("🎯 Custom Interview Questions to Prepare")
                for q in data.get("interview_questions", []):
                    st.markdown(f"- {q}")

            except Exception as e:
                st.error(f"Error analyzing document: {e}")
