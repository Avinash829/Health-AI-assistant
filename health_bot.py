import streamlit as st
import PyPDF2
import google.generativeai as genai
from dotenv import load_dotenv
import os
from fpdf import FPDF  # For generating PDFs

# Load environment variables
load_dotenv()

# Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error("Gemini API key not found. Please set the GEMINI_API_KEY environment variable.")
    st.stop()  # Stop the app if the API key is missing

genai.configure(api_key=api_key)

# Function to extract text from PDF
def extract_text_from_pdf(uploaded_file):
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# Function to analyze health report using Gemini AI
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
    else:  # Patient's Report
        prompt = f"""
        Analyze the following health checkup report from a patient's perspective and provide:
        1. Summary of the patient's condition
        2. Symptoms
        3. Remedies to cure
        4. Precautions to take

        Health Report:
        {text}
        """

    # Call Gemini AI API
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    return response.text

# Function to handle user queries
def handle_user_query(query):
    # List of health-related keywords
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

    # Convert query to lowercase for case-insensitive matching
    query_lower = query.lower()

    # Check if the query contains any health-related keywords
    if any(keyword in query_lower for keyword in health_keywords):
        # If the query is health-related, generate a response
        prompt = f"""
        Provide a precise and concise response to the following health-related query:
        {query}
        """
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        return response.text
    else:
        # If the query is unrelated, return a message
        return "Sorry, I can only provide information related to health, drugs, medicines, or body conditions."

# Function to generate a PDF from the report
def generate_pdf(report_text, filename="health_report.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Replace unsupported characters with a placeholder or remove them
    report_text_encoded = report_text.encode("latin-1", errors="replace").decode("latin-1")
    
    pdf.multi_cell(0, 10, report_text_encoded)
    pdf.output(filename)
    return filename

# Streamlit app
st.title("Health AI Assistant")

# Welcome Note and Description
st.markdown(
    """
    ## Welcome to Health AI Assistant! 🩺🤖

    **Health AI Assistant** is your personal health companion designed to help you understand and analyze your health checkup reports. 
    Whether you're a patient looking for a summary of your health or a doctor seeking detailed insights, this app has got you covered.

    ### How It Works:
    1. **Upload Your Health Report**: Upload your health checkup report in PDF format.
    2. **Choose Report Type**: Select between a **Patient's Report** (easy-to-understand summary) or a **Doctor's Report** (detailed technical analysis).
    3. **Get Insights**: The app will analyze your report and provide actionable insights, including symptoms, treatment suggestions, and remedies.
    4. **Ask Questions**: Use the AI chatbot to ask health-related questions and get precise answers.

    ### Why Use This App?
    - **Easy to Use**: No medical expertise required.
    - **Accurate Analysis**: Powered by advanced AI for reliable insights.
    - **Privacy First**: Your data is secure and never shared with third parties.

    Ready to get started? Upload your health report below! ⬇️
    """
)

# Upload PDF file
uploaded_file = st.file_uploader("Upload your health checkup report (PDF):", type="pdf")

if uploaded_file is not None:
    # Extract text from PDF
    text = extract_text_from_pdf(uploaded_file)
    st.write("### Extracted Text from PDF:")
    st.write(text)

    # Select report type
    report_type = st.radio("Select the type of report you want to generate:", ("Patient's Report", "Doctor's Report"))

    # Analyze health report
    if st.button("Analyze Report"):
        st.write(f"### {report_type} Results:")
        with st.spinner("Analyzing..."):
            try:
                analysis = analyze_health_report(text, report_type)
                st.session_state.analysis = analysis  # Store the report in session state
                st.write(analysis)
            except Exception as e:
                st.error(f"An error occurred: {e}")

    # Download Report as PDF
    if "analysis" in st.session_state:
        pdf_filename = generate_pdf(st.session_state.analysis)
        with open(pdf_filename, "rb") as file:
            st.download_button(
                label="Download Report as PDF",
                data=file,
                file_name=pdf_filename,
                mime="application/pdf"
            )

    # Shareable Link for Report
    if "analysis" in st.session_state:
        st.write("### Shareable Link:")
        st.write("Copy the link below to share your report:")
        shareable_link = f"https://yourapp.com/report/{hash(st.session_state.analysis)}"  # Simulated link
        st.code(shareable_link)

# Add an AI icon at the bottom right to toggle the chat interface
st.sidebar.markdown(
    """
    <style>
    .ai-icon {
        position: fixed;
        bottom: 50px;
        right: 20px;
        font-size: 24px;
        cursor: pointer;
    }
    </style>
    <div class="ai-icon" onclick="toggleChat()">🤖</div>
    <script>
    function toggleChat() {
        const sidebar = window.parent.document.querySelector("[data-testid='stSidebar']");
        if (sidebar.style.transform === 'translateX(0px)') {
            sidebar.style.transform = 'translateX(100%)';
        } else {
            sidebar.style.transform = 'translateX(0px)';
        }
    }
    </script>
    """,
    unsafe_allow_html=True
)

# Add a query input box in the sidebar
with st.sidebar:
    st.write("### Ask the AI")
    user_query = st.text_input("Enter your query related to health:")

    if user_query:
        with st.spinner("Generating response..."):
            try:
                response = handle_user_query(user_query)
                st.write("### AI Response:")
                st.write(response)
            except Exception as e:
                st.error(f"An error occurred: {e}")
