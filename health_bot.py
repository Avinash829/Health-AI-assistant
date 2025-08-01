import streamlit as st
import PyPDF2
import google.generativeai as genai
from dotenv import load_dotenv
import os
from fpdf import FPDF

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error("Gemini API key not found. Please set the GEMINI_API_KEY environment variable.")
    st.stop()

genai.configure(api_key=api_key)

def extract_text_from_pdf(uploaded_file):
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def generate_pdf(report_text, filename="health_report.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    report_text_encoded = report_text.encode("latin-1", errors="replace").decode("latin-1")
    pdf.multi_cell(0, 10, report_text_encoded)
    pdf.output(filename)
    return filename

# Report Analysis
def analyze_health_report(text, report_type):
    if report_type == "Doctor's Report":
        prompt = f"""
        Analyze the following health checkup report from a doctor's perspective and provide:
        1. Detailed symptoms
        2. Technical explanation of the patient's condition
        3. Treatment suggested
        4. Medicines suggested with prescription details
        5. Severity of the condition

        Health Report:
        {text}
        """
    else:
        prompt = f"""
        Analyze the following health checkup report from a patient's perspective and provide:
        1. Summary of the patient's condition
        2. Symptoms
        3. Remedies to cure
        4. Precautions to take

        Health Report:
        {text}
        """

    model = genai.GenerativeModel("gemini-2.0")
    response = model.generate_content(prompt)
    return response.text.strip()

# AI Chat Query Handler
def handle_user_query(query, doctor_mode=False):
    health_keywords = [
        "health", "drug", "medicine", "body", "symptom", "treatment", "cure", "precaution", 
        "disease", "condition", "pain", "illness", "diagnosis", "prescription", "pharmacy", 
        "vitamin", "supplement", "exercise", "diet", "nutrition", "therapy", "recovery", 
        "infection", "allergy", "blood", "heart", "lung", "liver", "kidney", "bone", 
        "muscle", "nerve", "skin", "mental", "stress", "anxiety", "depression", "fever", 
        "cough", "headache", "stomach", "digestion", "sleep", "weight", "hypertension", 
        "diabetes", "cholesterol", "cancer", "asthma", "arthritis", "injury", "wound", 
        "surgery", "vaccine", "antibiotic", "antiviral", "antifungal", "probiotic", 
        "hormone", "thyroid", "pregnancy", "childbirth", "menopause", "elderly", "pediatric"
    ]

    query_lower = query.lower()

    if not any(keyword in query_lower for keyword in health_keywords):
        return "This assistant specializes in health and medical information. Please ask a question related to your body, health, symptoms, or wellness 😊."

    if doctor_mode:
        prompt = f"""
        You are an AI assistant for medical professionals. Answer the question with accurate, technical detail and use clinical terminology when appropriate.

        Question: {query}
        """
    else:
        prompt = f"""
        You are a professional and friendly AI health assistant. Give helpful, clear, and safe responses for the general public.

        Guidelines:
        - Keep answers understandable for a non-medical person.
        - Be empathetic and suggest doctor visits if needed.
        - Include practical advice when applicable.

        Examples:
        Q: What causes frequent headaches?
        A: Frequent headaches can result from stress, eye strain, poor posture, dehydration, or underlying medical conditions. If they persist or worsen, it's important to consult a neurologist.

        Q: How to treat mild fever at home?
        A: For a mild fever, rest, drink plenty of fluids, and take paracetamol if needed. If it lasts more than 2 days or gets very high, see a doctor.

        Now answer this:
        Q: {query}
        """

    try:
        model = genai.GenerativeModel("gemini-2.0")
        response = model.generate_content(prompt)
        answer = response.text.strip()

        if not answer or "I'm not sure" in answer or "Sorry" in answer:
            return "I'm sorry, I couldn't generate a helpful response. Please rephrase your question or consult a healthcare professional."

        return answer

    except Exception as e:
        return f"An error occurred while generating the response: {e}"

# Streamlit UI
st.set_page_config(page_title="Health AI Assistant", layout="wide")
st.title("Health AI Assistant 🩺🤖")

st.markdown(
    """
    ## Welcome to Health AI Assistant!

    Upload your health report, choose a report type, and get actionable AI-driven insights.
    """
)

uploaded_file = st.file_uploader("Upload your health checkup report (PDF):", type="pdf")

if uploaded_file:
    text = extract_text_from_pdf(uploaded_file)
    st.write("### Extracted Text from PDF:")
    st.write(text)

    report_type = st.radio("Select the type of report you want to generate:", ("Patient's Report", "Doctor's Report"))

    if st.button("Analyze Report"):
        st.write(f"### {report_type} Results:")
        with st.spinner("Analyzing your report..."):
            try:
                analysis = analyze_health_report(text, report_type)
                st.session_state.analysis = analysis
                st.write(analysis)
            except Exception as e:
                st.error(f"An error occurred: {e}")

    if "analysis" in st.session_state:
        pdf_filename = generate_pdf(st.session_state.analysis)
        with open(pdf_filename, "rb") as file:
            st.download_button(
                label="Download Report as PDF",
                data=file,
                file_name=pdf_filename,
                mime="application/pdf"
            )

        st.write("### Shareable Link:")
        st.code(f"https://yourapp.com/report/{hash(st.session_state.analysis)}")

with st.sidebar:
    st.write("### 💬 Ask the AI Assistant")
    doctor_mode = st.toggle("👨‍⚕️ Doctor Mode", value=False)
    user_query = st.text_input("Enter your health-related question:")

    if user_query:
        with st.spinner("Generating response..."):
            try:
                response = handle_user_query(user_query, doctor_mode)
                st.write("### AI Response:")
                st.write(response)
            except Exception as e:
                st.error(f"An error occurred: {e}")
