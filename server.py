from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import os
import requests


app = Flask(__name__)
CORS(app)
# Configure Gemini AI
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Shopify environment variables
SHOPIFY_STORE = os.getenv("SHOPIFY_STORE")
SHOPIFY_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
SHOPIFY_API_VERSION = os.getenv("SHOPIFY_API_VERSION", "2025-07")

# Fetch all products from Shopify
def get_shopify_products():
    url = f"{SHOPIFY_STORE}/admin/api/{SHOPIFY_API_VERSION}/products.json"
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_TOKEN,
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("products", [])
    return []

# Find a product that matches a query
def find_product(query, products):
    query_lower = query.lower()
    for product in products:
        if product['title'].lower() in query_lower:
            variant = product['variants'][0] if product['variants'] else {}
            return {
                "title": product['title'],
                "description": product.get('body_html', 'No description available'),
                "price": variant.get('price', '0.00'),
                "image": product.get('image', {}).get('src', '')
            }
    return None

@app.route("/")
def home():
    return "✅ LayerLabs Shopify Chatbot is running!"

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "")

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    # Step 1: Check Shopify products
    products = get_shopify_products()
    product_info = find_product(user_message, products)

    if product_info:
        reply = f"Product: {product_info['title']}\nPrice: ${product_info['price']}\nDescription: {product_info['description']}\nImage: {product_info['image']}"
        return jsonify({"reply": reply})

    # Step 2: Fallback to Gemini AI
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(user_message)

    return jsonify({"reply": response.text})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
