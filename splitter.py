from dotenv import load_dotenv
load_dotenv()

import json
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

# Load the scraped docs from disk
# No need to re-scrape — we use the JSON we saved earlier
with open("scraped_docs.json", "r", encoding="utf-8") as f:
    raw_data = json.load(f)

print(f"Loaded {len(raw_data)} pages from scraped_docs.json")

# Convert raw JSON back into LangChain Document objects
# Document has two fields:
#   page_content → the text
#   metadata     → dict of extra info (we store the source URL here)
docs = [
    Document(
        page_content=item["content"],
        metadata={"source": item["source"]}
    )
    for item in raw_data
]

# RecursiveCharacterTextSplitter is the recommended splitter for RAG
# It tries to split on paragraphs first, then sentences, then words
# Only splits on characters as a last resort — hence "Recursive"
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,      # each chunk is max 500 characters
    chunk_overlap=50,    # 50 characters repeated between chunks
)

# Split all documents into chunks
# Each chunk is still a Document object
# It inherits the metadata (source URL) from its parent document
chunks = splitter.split_documents(docs)

print(f"Total chunks created: {len(chunks)}")
print(f"Average chunk size: {sum(len(c.page_content) for c in chunks) // len(chunks)} chars")

# Preview first 3 chunks so we can verify the splitting looks right
for i, chunk in enumerate(chunks[:3]):
    print(f"\n--- Chunk {i+1} ---")
    print(f"Source: {chunk.metadata['source']}")
    print(f"Length: {len(chunk.page_content)} chars")
    print(f"Content: {chunk.page_content}")