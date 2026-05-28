from dotenv import load_dotenv
load_dotenv()

from langchain_community.document_loaders.recursive_url_loader import RecursiveUrlLoader
from bs4 import BeautifulSoup
from html import unescape
import re
import json


def extract_clean_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    
    main = soup.find(id="MainContent")
    
    if main:
        for tag in main(["script", "style"]):
            tag.decompose()
        for tag in main.find_all(class_=[
            "quantity", "cart-notification", 
            "product-form__input", "no-js-hidden"
        ]):
            tag.decompose()
        text = main.get_text(separator=" ", strip=True)
    else:
        for tag in soup(["nav", "footer", "script", "style", "header"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
    
    text = re.sub(r'\d+\s*/\s*of\s*\d+', '', text)
    text = re.sub(r'\(\s*\d+\s*in cart\s*\)', '', text)
    text = re.sub(r'Decrease quantity for.*?Increase quantity for[^a-z]*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'(Increase|Decrease) quantity for[^\n]*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Quantity', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Unit price\s*/\s*per', '', text)
    text = re.sub(r'Shipping calculated at checkout\.?', '', text)
    text = re.sub(r'Sold out', '', text)
    text = re.sub(r'Sale price|Regular price|Sale', '', text)
    text = re.sub(r'Open media \d+ in modal', '', text)
    text = re.sub(r'Skip to (content|product information)', '', text)
    text = re.sub(r'(Free Shipping Above ₹\d+\s*[•·]?\s*)+', '', text)
    text = re.sub(r'Item added to your cart', '', text)
    text = re.sub(r'View cart|Check out|Continue shopping', '', text)
    text = unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def should_include(url: str, content: str) -> bool:
    skip_extensions = [".css", ".js", ".png", ".jpg", ".jpeg", ".svg", ".woff", ".woff2"]
    for ext in skip_extensions:
        if url.endswith(ext) or ext + "?" in url:
            return False
    if "/cdn/shop/" in url:
        return False
    
    # Skip pages with almost no content — empty collections, error pages
    if len(content.strip()) < 100:
        return False
    
    return True


headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

print("Starting scrape...")

loader = RecursiveUrlLoader(
    url="https://layerlabs.in",
    max_depth=2,
    extractor=extract_clean_text,
    headers=headers,
    exclude_dirs=[
        "https://layerlabs.in/cdn",
        "https://layerlabs.in/cart",
        "https://layerlabs.in/account",
        "https://layerlabs.in/search",
    ]
)

raw_docs = loader.load()
print(f"Raw docs loaded: {len(raw_docs)}")

docs = [doc for doc in raw_docs if should_include(doc.metadata["source"], doc.page_content)]
print(f"Docs after filtering: {len(docs)}")

for i, doc in enumerate(docs[:5]):
    print(f"\nPage {i+1}: {doc.metadata['source']}")
    print(f"Content length: {len(doc.page_content)} chars")
    print(f"Preview: {doc.page_content[:300]}")

# Save scraped docs to disk so we don't re-scrape during development
data = [
    {
        "source": doc.metadata["source"],
        "content": doc.page_content
    }
    for doc in docs
]

with open("scraped_docs.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\nSaved {len(data)} docs to scraped_docs.json")