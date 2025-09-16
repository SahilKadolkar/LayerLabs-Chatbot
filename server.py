from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests

app = Flask(__name__)
CORS(app)

# Shopify config
SHOP_NAME = os.getenv("SHOP_NAME")  # e.g., "y4n8mm-1g"
ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")  # e.g., "shpat_..."

def get_shopify_products():
    """Fetch products from Shopify and return a dictionary with title as key."""
    url = f"https://{SHOP_NAME}.myshopify.com/admin/api/2025-07/products.json"
    headers = {
        "X-Shopify-Access-Token": ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        products = {}
        for product in data.get("products", []):
            title = product.get("title", "").lower()
            price = product.get("variants")[0].get("price", "0.00") if product.get("variants") else "0.00"
            description = product.get("body_html", "No description available.")
            products[title] = {
                "title": product.get("title", ""),
                "price": price,
                "description": description
            }
        return products
    except Exception as e:
        print("Error fetching products:", e)
        return {}

@app.route("/")
def home():
    return "✅ LayerLabs Shopify Chatbot is running!"

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "").lower()
    products = get_shopify_products()

    # Handle greetings
    greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
    if any(greet in user_message for greet in greetings):
        return jsonify({"reply": "Hello! 👋 How can I help you today? You can ask me about our products or orders."})

    # Check for product queries
    for name, info in products.items():
        if name in user_message:
            return jsonify({
                "reply": f"Product: {info['title']}\n"
                         f"Price: ${info['price']}\n"
                         f"Description: {info['description']}"
            })

    # Fallback response
    return jsonify({"reply": "Sorry, I didn't understand that. You can ask me about our products or orders."})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
