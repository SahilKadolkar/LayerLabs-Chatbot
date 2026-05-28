from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser

# Step 1 — Initialize FastAPI app
# FastAPI is the web framework — it listens for HTTP requests
# and routes them to the right function
app = FastAPI()

# Step 2 — CORS middleware
# CORS = Cross Origin Resource Sharing
# Your Shopify store is at layerlabs.in
# Your backend will be at layerlabs-chatbot.onrender.com
# By default browsers BLOCK requests between different domains
# This middleware tells the browser "it's okay, allow these domains"
# Without this your widget.js cannot talk to your backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://layerlabs.in",        # your Shopify store
        "http://localhost:3000",        # for local testing
        "http://localhost:8000",        # for local testing
    ],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# Step 3 — Load vector store once when server starts
# We load FAISS here at startup — not inside the endpoint function
# If we loaded inside the endpoint, it would reload on EVERY request
# That would be extremely slow — 2-3 seconds per query just for loading
# Loading once at startup = instant retrieval on every request
print("Loading vector store...")
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = FAISS.load_local(
    "faiss_index",
    embeddings,
    allow_dangerous_deserialization=True
)
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 4}
)
print("Vector store loaded")

# Step 4 — Build the RAG chain
# Exact same chain as chain.py
# Defined once at startup, reused for every request
prompt = PromptTemplate.from_template("""
You are a helpful customer support assistant for LayerLabs —
a D2C brand that sells 3D printed products like lamps, clocks,
planters, keychains, and figurines.

Answer the customer's question using ONLY the context provided below.
If the answer is not in the context, say "I don't have that information
right now. Please contact us at layerlabs.in for help."
Do not make up prices, colors, or product details.

Context:
{context}

Customer question: {question}

Answer:
""")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def format_docs(docs):
    return "\n\n---\n\n".join(doc.page_content for doc in docs)

chain = (
    {
        "context": retriever | format_docs,
        "question": RunnablePassthrough()
    }
    | prompt
    | llm
    | StrOutputParser()
)

# Step 5 — Define request and response models
# Pydantic models validate incoming request data automatically
# If someone sends a request without a "question" field
# FastAPI returns a clear error instead of crashing
class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str

# Step 6 — Define the chat endpoint
# @app.post("/chat") means:
#   - Listen for POST requests at the /chat URL
#   - When one arrives, run this function
#   - Return the result as JSON
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # request.question is the customer's message
    # chain.invoke() runs the full RAG pipeline
    answer = chain.invoke(request.question)
    return ChatResponse(answer=answer)

# Step 7 — Health check endpoint
# A simple GET endpoint that returns ok
# Render and other hosting platforms ping this to verify
# your server is running. If it returns 200, server is healthy.
@app.get("/health")
async def health():
    return {"status": "ok"}