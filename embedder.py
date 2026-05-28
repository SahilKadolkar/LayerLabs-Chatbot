from dotenv import load_dotenv
load_dotenv()

import json
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document

# Step 1 — Load chunks from disk
# We saved scraped_docs.json in loader.py
# We'll re-split here so embedder.py is self-contained
# This way you can run embedder.py independently anytime
with open("scraped_docs.json", "r", encoding="utf-8") as f:
    raw_data = json.load(f)

print(f"Loaded {len(raw_data)} pages from scraped_docs.json")

# Step 2 — Convert to Document objects and split
# Same logic as splitter.py — we repeat it here so this file
# can run standalone without depending on splitter.py
from langchain.text_splitter import RecursiveCharacterTextSplitter

docs = [
    Document(
        page_content=item["content"],
        metadata={"source": item["source"]}
    )
    for item in raw_data
]

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
)
chunks = splitter.split_documents(docs)
print(f"Total chunks to embed: {len(chunks)}")

# Step 3 — Initialize the embedding model
# OpenAIEmbeddings calls OpenAI's API to convert text → vectors
# model="text-embedding-3-small" is the cheapest and fastest
# It produces 1536-dimensional vectors
# This line does NOT make any API call yet — just configuration
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# Step 4 — Create the FAISS vector store
# THIS is where the OpenAI API gets called
# It sends all 136 chunks to OpenAI's embedding API
# Gets back 136 vectors (lists of 1536 numbers)
# Stores them in FAISS in memory
# This will cost a tiny amount — roughly $0.000001 per chunk
# 136 chunks = less than 1 paisa total
print("Embedding chunks... this may take 30-60 seconds")
vectorstore = FAISS.from_documents(chunks, embeddings)
print("Embedding complete")

# Step 5 — Save the FAISS index to disk
# FAISS is in-memory by default — if you don't save it,
# you lose it when the script ends
# save_local() creates a folder with two files:
#   faiss_index/index.faiss  → the actual vectors
#   faiss_index/index.pkl    → the chunk texts and metadata
vectorstore.save_local("faiss_index")
print("Vector store saved to faiss_index/")

# Step 6 — Quick test to verify everything works
# Load the index back from disk
# allow_dangerous_deserialization=True is required by LangChain
# as a safety acknowledgment when loading pickle files
print("\nTesting retrieval...")
loaded_vectorstore = FAISS.load_local(
    "faiss_index",
    embeddings,
    allow_dangerous_deserialization=True
)

# similarity_search takes a plain text query
# converts it to a vector internally
# finds the 3 most similar chunks in FAISS
# returns them as Document objects
test_query = "what colors does the perch clock come in"
results = loaded_vectorstore.similarity_search(test_query, k=3)

print(f"\nTop 3 results for: '{test_query}'")
for i, result in enumerate(results):
    print(f"\nResult {i+1}:")
    print(f"Source: {result.metadata['source']}")
    print(f"Content: {result.page_content[:200]}")