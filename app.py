import os
import re
import streamlit as st
import google.generativeai as genai
from fpdf import FPDF

# --- CUSTOM CSS ---
def local_css():
    st.markdown(
        """
        <style>
        /* Page background */
        .stApp {
            background: linear-gradient(to right, #eef2f3, #dfe6e9);
            font-family: 'Segoe UI', sans-serif;
        }

        /* Title */
        h1 {
            color: #2C3E50;
            text-align: center;
            font-family: 'Segoe UI', sans-serif;
            font-size: 2.5em;
            font-weight: bold;
            text-shadow: 1px 1px 3px rgba(0,0,0,0.2);
            margin-bottom: 20px;
        }

        /* Input boxes */
        .stTextInput > div > div > input {
            border-radius: 12px;
            border: 1px solid #bbb;
            padding: 10px;
            box-shadow: 0px 1px 5px rgba(0,0,0,0.1);
        }

        /* Dropdowns */
        .stSelectbox > div > div {
            border-radius: 12px;
            border: 1px solid #bbb;
            padding: 5px;
            box-shadow: 0px 1px 5px rgba(0,0,0,0.1);
        }

        /* Buttons */
        .stButton button {
            background: linear-gradient(to right, #4CAF50, #45a049);
            color: white;
            border-radius: 8px;
            padding: 12px 24px;
            font-weight: bold;
            border: none;
            transition: 0.3s;
            box-shadow: 0px 4px 10px rgba(0,0,0,0.2);
        }
        .stButton button:hover {
            background: linear-gradient(to right, #45a049, #3e8e41);
            transform: scale(1.05);
        }

        /* Result cards */
        .card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin: 15px 0;
            box-shadow: 0px 4px 15px rgba(0,0,0,0.1);
        }
        .card h3 {
            color: #2C3E50;
            margin-bottom: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

local_css()

# --- CONFIGURE GEMINI ---
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_ID = "models/gemini-2.5-flash"
model = genai.GenerativeModel(MODEL_ID)

# --- CLEANUP FUNCTION ---
def clean_text(text):
    text = text.replace("—", "-")   
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("’", "'")
    return re.sub(r'[^\x00-\x7F]+', ' ', text)

# --- PDF CLASS ---
class PDF(FPDF):
    def header(self):
        self.set_font("DejaVu", "B", 14)
        self.cell(0, 10, "Educational Article / Study Guide", ln=True, align="C")
        self.ln(5)

    def chapter_title(self, title):
        self.set_font("DejaVu", "B", 12)
        self.set_text_color(30, 30, 120)
        self.multi_cell(0, 10, clean_text(title))
        self.ln(2)

    def chapter_body(self, body):
        self.set_font("DejaVu", "", 11)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 8, clean_text(body.strip()))
        self.ln()

# --- SAVE TO PDF ---
def save_pdf(title, sections, filename="output.pdf"):
    pdf = PDF()
    pdf.add_font("DejaVu", "", "DejaVuLGCSans.ttf", uni=True)
    pdf.add_font("DejaVu", "B", "DejaVuLGCSans-Bold.ttf", uni=True)
    pdf.add_page()
    pdf.set_font("DejaVu", "B", 16)
    pdf.cell(0, 10, clean_text(title), ln=True, align="C")
    pdf.ln(10)
    for sec_title, sec_body in sections.items():
        pdf.chapter_title(sec_title)
        pdf.chapter_body(sec_body)
    pdf.output(filename)
    return filename

# --- STREAMLIT UI ---
st.set_page_config(page_title="Educational Article Generator", page_icon="📘", layout="centered")
st.title("📘 Educational Article / Study Guide Generator")

topic = st.text_input("Enter a topic or keywords (comma separated):", placeholder="e.g. Solar System, Python Basics")
depth = st.selectbox("Select depth:", ["Beginner", "Intermediate", "Advanced"])
tone = st.selectbox("Select tone:", ["Academic", "Simple", "Conversational"])

if st.button("Generate Article"):
    if not topic:
        st.warning("⚠️ Please enter a topic first!")
    else:
        with st.spinner("✍️ Generating article..."):
            try:
                prompt = f"""
                Create a structured study guide on the following topics: {topic}.
                - Depth: {depth}
                - Tone: {tone}
                - Include sections: Introduction, Explanation with examples, and Further Reading.
                - Format output clearly with section headings (use Markdown style ## Heading).
                """
                response = model.generate_content(prompt)
                output_text = response.text

                # --- Parse into sections ---
                sections = {}
                current_title = "Introduction"
                sections[current_title] = ""
                for line in output_text.splitlines():
                    if line.strip().startswith("##"):
                        current_title = line.replace("#", "").strip()
                        sections[current_title] = ""
                    else:
                        sections[current_title] += line + "\n"

                # --- Show results inside cards ---
                for title, body in sections.items():
                    st.markdown(f"<div class='card'><h3>{title}</h3><p>{body}</p></div>", unsafe_allow_html=True)

                # --- PDF Download ---
                pdf_file = save_pdf("Study Guide", sections)
                with open(pdf_file, "rb") as f:
                    st.download_button("📥 Download PDF", f, file_name="study_guide.pdf", mime="application/pdf")

            except Exception as e:
                st.error(f"❌ Error: {e}")
