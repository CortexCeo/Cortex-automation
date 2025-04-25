import os
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from dotenv import load_dotenv

load_dotenv()

def get_gemini(model):
    llm = ChatGoogleGenerativeAI(model=model, google_api_key = os.getenv("GEMINI_API_KEY_BETA"), disable_streaming=False)
    return llm

def initialize_langchain_embedding_model():
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key = os.getenv("GEMINI_API_KEY_BETA"))
    return embeddings


gemini_flash = get_gemini("gemini-2.0-flash")
gemini_embeddings = initialize_langchain_embedding_model()