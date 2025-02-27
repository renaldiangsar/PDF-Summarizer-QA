import streamlit as st
import requests
import tempfile

# FastAPI backend URL
API_URL = "http://127.0.0.1:8000"

st.title("📄 PDF Summarizer & QA Chatbot")

# File upload (single upload for both sections)
st.sidebar.header("Upload PDF")
uploaded_file = st.sidebar.file_uploader("Upload a PDF file", type=["pdf"], key="pdf_upload")

if uploaded_file:
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(uploaded_file.getvalue())
        temp_file_path = temp_file.name
else:
    temp_file_path = None

# Sidebar navigation
st.sidebar.title("Navigation")
section = st.sidebar.radio("Go to", ("Summarization", "Q&A"))

if section == "Summarization":
    st.header("📑 Summarize the PDF")
    if uploaded_file is not None:
        if st.button("Summarize"): 
            with open(temp_file_path, "rb") as f:
                files = {"file": f}
                response = requests.post(f"{API_URL}/summarize/", files=files)
            
            if response.status_code == 200:
                summary = response.json()["summary"]
                st.subheader("Summary:")
                st.write(summary)
            else:
                st.error("Failed to summarize the PDF.")
    else:
        st.warning("Please upload a PDF file first.")

elif section == "Q&A":
    st.header("💬 Ask a Question from PDF")
    query = st.text_input("Enter your question:")
    
    if uploaded_file is not None and query:
        if st.button("Get Answer"):
            with open(temp_file_path, "rb") as f:
                files = {"file": f}
                data = {"query": query}
                response = requests.post(f"{API_URL}/ask/", files=files, data=data)
            
            if response.status_code == 200:
                answer = response.json()["answer"]
                st.subheader("Answer:")
                st.write(answer)
            else:
                st.error("Failed to process the question.")
    elif uploaded_file is None:
        st.warning("Please upload a PDF file first.")
    elif not query:
        st.warning("Please enter a question.")