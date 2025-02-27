from fastapi import FastAPI, UploadFile, File, Form
import uvicorn
from langchain_groq import ChatGroq
from langchain.chains.summarize import load_summarize_chain
from langchain.chains import RetrievalQA
from langchain_community.document_loaders import PyPDFLoader
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
import shutil
import os
from pathlib import Path

load_dotenv()
app = FastAPI()

# Load OpenAI model
groq_api_key=os.getenv("GROQ_API_KEY")
llm=ChatGroq(model="gemma2-9b-it",groq_api_key=groq_api_key)
os.environ['HF_TOKEN']=os.getenv("HF_TOKEN")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Define a custom prompt template for summarization
prompt_template = PromptTemplate(
    input_variables=["text"],
    template=("Summarize the following document while keeping the key details, important points, and main insights."
              "Every key details, important points, and main insights should have one paragraph of explanation"
              "if document long or have a many words, give summary atleast 1000 words."
              "Ensure that the summary is clear and structured"
              "Maintain enough context for full understanding. \n\n{text}")
)

# Define a custom chat prompt template for QA
aq_prompt_template = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant that answers questions based on the given document."),
    ("human", "Context: {context}\n\nQuery: {query}")
])

@app.post("/summarize/")
async def summarize_pdf(file: UploadFile = File(...)):
    temp_file = Path(f"temp_{file.filename}")
    with temp_file.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    loader = PyPDFLoader(str(temp_file))
    documents = loader.load()
    
    chain = load_summarize_chain(llm, chain_type="refine", refine_prompt=prompt_template)
    summary = chain.invoke(documents)

    summary_text = summary.get("output_text", "") if isinstance(summary, dict) else str(summary)
    
    temp_file.unlink()  # Delete temporary file
    
    return {"summary": summary_text}

@app.post("/ask/")
async def ask_pdf(file: UploadFile = File(...), query: str = Form(...)):
    temp_file = Path(f"temp_{file.filename}")
    with temp_file.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    loader = PyPDFLoader(str(temp_file))
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=5000, chunk_overlap=500)
    texts = text_splitter.split_documents(documents)
    
    vectorstore = FAISS.from_documents(texts, embeddings)
    retriever = vectorstore.as_retriever()
    qa_chain = RetrievalQA.from_chain_type(llm, retriever=retriever, chain_type="stuff", return_source_documents=False)
    
    answer = qa_chain.invoke({"context": texts, "query": query, "prompt": aq_prompt_template})
    answer_qa = answer.get("result", "") if isinstance(answer, dict) else str(answer)

    temp_file.unlink()
    
    return {"answer": answer_qa}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)