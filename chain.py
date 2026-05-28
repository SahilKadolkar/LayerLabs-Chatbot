from dotenv import load_dotenv
load_dotenv()

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser

# Step 1 — Load the FAISS index we saved in embedder.py
# We need the same embedding model used during indexing
# If you use a different model here the vectors won't match
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

vectorstore = FAISS.load_local(
    "faiss_index",
    embeddings,
    allow_dangerous_deserialization=True
)
print("Vector store loaded successfully")

# Step 2 — Create a retriever from the vector store
# A retriever is just a standard interface around FAISS
# search_type="similarity" → find chunks by vector similarity
# k=4 → return top 4 most relevant chunks per query
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 4}
)

# Step 3 — Define the prompt template
# This is the exact instruction we give GPT-4o-mini
# {context} → will be filled with the 4 retrieved chunks
# {question} → will be filled with the user's question
# The instruction to answer only from context is critical
# Without it the LLM uses its general knowledge and hallucinates
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

# Step 4 — Initialize the LLM
# temperature=0 means deterministic — same question always gets
# same answer. Good for customer support where consistency matters.
# temperature=1 would be more creative but inconsistent.
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)

# Step 5 — A helper function to format retrieved chunks
# The retriever returns a list of Document objects
# The prompt expects a single string for {context}
# This function joins all chunk texts with a separator
def format_docs(docs):
    return "\n\n---\n\n".join(doc.page_content for doc in docs)

# Step 6 — Build the chain
# This is LangChain's LCEL syntax (LangChain Expression Language)
# Read it as a pipeline using the | pipe operator:
#
# {context: retrieve and format chunks, question: pass through as-is}
#       ↓
# fill into prompt template
#       ↓
# send to GPT-4o-mini
#       ↓
# extract the text string from the response
#
# RunnablePassthrough() means "pass the input unchanged"
# It lets the question flow through to the prompt untouched
chain = (
    {
        "context": retriever | format_docs,
        "question": RunnablePassthrough()
    }
    | prompt
    | llm
    | StrOutputParser()
)

# Step 7 — Test the chain with real questions
print("\n--- Testing the RAG chain ---\n")

test_questions = [
    "What colors does the Perch wall clock come in?",
    "What is your refund policy?",
    "How much does the mellow lamp cost?",
    "Do you sell custom figurines?",
]

for question in test_questions:
    print(f"Q: {question}")
    answer = chain.invoke(question)
    print(f"A: {answer}")
    print()