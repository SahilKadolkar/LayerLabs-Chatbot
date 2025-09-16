# server.py
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os, requests, json, re
import google.generativeai as genai

# ---------- Config ----------
app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# Environment (set these in Render)
SHOPIFY_STORE = os.getenv("SHOPIFY_STORE")  # e.g. https://yourstore.myshopify.com
SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
SHOPIFY_API_VERSION = os.getenv("SHOPIFY_API_VERSION", "2025-07")  # change if needed
GENIE_API_KEY = os.getenv("GEMINI_API_KEY")

# configure Gemini
genai.configure(api_key=GENIE_API_KEY)
model = genai.GenerativeModel("gemini-pro")

# Helper: GraphQL call to Shopify
def shopify_graphql(query, variables=None):
    url = f"{SHOPIFY_STORE}/admin/api/{SHOPIFY_API_VERSION}/graphql.json"
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    resp = requests.post(url, headers=headers, json=payload, timeout=20)
    resp.raise_for_status()
    return resp.json()

# Product search via GraphQL
PRODUCTS_QUERY = """
query($q: String!) {
  products(first: 6, query: $q) {
    edges {
      node {
        id
        title
        handle
        descriptionHtml
        vendor
        tags
        images(first:3) { edges { node { transformedSrc } } }
        variants(first:5) { edges { node { sku price } } }
      }
    }
  }
}
"""

def search_products_by_text(text):
    # Try a product title query (GraphQL query arg uses Shopify search syntax).
    q = text  # you can craft: f'title:"{text}"' for exact-match attempts
    data = shopify_graphql(PRODUCTS_QUERY, {"q": q})
    edges = data.get("data", {}).get("products", {}).get("edges", [])
    results = [e["node"] for e in edges]
    return results

# Orders search via GraphQL (search by name and optional email)
ORDERS_QUERY = """
query($q: String!) {
  orders(first: 1, query: $q) {
    nodes {
      id
      name
      orderNumber
      email
      processedAt
      fulfillmentStatus
      financialStatus
      totalPriceSet { shopMoney { amount currencyCode } }
      lineItems(first:10) { edges { node { title quantity } } }
      shippingAddress { firstName lastName address1 city province country zip phone }
    }
  }
}
"""

def find_order(name_or_number, email=None):
    q = f'name:{name_or_number}'
    if email:
        q = f'{q} AND email:{email}'
    data = shopify_graphql(ORDERS_QUERY, {"q": q})
    nodes = data.get("data", {}).get("orders", {}).get("nodes", [])
    return nodes[0] if nodes else None

# Basic intent+entity extractor using Gemini; fallback to small rules
def parse_intent_and_entities(user_message):
    # Prompt Gemini to return strict JSON: { "intent": "...", "entities": {...} }
    prompt = (
        'Extract intent and entities from the user message. Return ONLY valid JSON.\n'
        'Respond with an object: {"intent": "<one of: product_info, order_status, order_tracking, greeting, fallback>", '
        '"entities": {"product": "...", "order_number": "...", "email":"..."} }\n\n'
        f'User message: """{user_message}"""'
    )
    try:
        resp = model.generate_content(prompt)
        text = resp.text.strip()
        # try to parse JSON strictly
        parsed = json.loads(text)
        intent = parsed.get("intent")
        entities = parsed.get("entities", {})
        return intent, entities
    except Exception:
        # fallback simple rules
        low = user_message.lower()
        if re.search(r'\b(order|#\d+|tracking)\b', low):
            # try extract order # and email
            order_m = re.search(r'#?(\d{3,10})', user_message)
            email_m = re.search(r'[\w\.-]+@[\w\.-]+', user_message)
            return "order_status", {"order_number": order_m.group(1) if order_m else None, "email": email_m.group(0) if email_m else None}
        if re.search(r'\b(product|price|tell me about|description|details)\b', low):
            return "product_info", {"product": user_message}
        if any(g in low for g in ["hello", "hi", "hey"]):
            return "greeting", {}
        return "fallback", {}

# Chat endpoint
@app.route("/chat", methods=["POST"])
def chat():
    payload = request.get_json() or {}
    user_message = payload.get("message", "")
    session_id = payload.get("session_id")  # optional
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    intent, entities = parse_intent_and_entities(user_message)

    try:
        if intent == "product_info":
            # either entity has product name, else use user message
            product_query_text = entities.get("product") or user_message
            prods = search_products_by_text(product_query_text)
            if not prods:
                return jsonify({"reply": f"Sorry, I couldn't find products matching \"{product_query_text}\". Can you try the exact product name?"})
            # take first match
            p = prods[0]
            # use Gemini to create a friendly response using product summary
            compose_prompt = (
                f"Create a short, friendly product reply to a customer based on this product JSON:\n\n{json.dumps(p)}\n\n"
                "Include title, short description, price/variants if available, and a CTA (e.g., 'View product'). Keep it under 120 words."
            )
            gen = model.generate_content(compose_prompt)
            return jsonify({"reply": gen.text})

        elif intent in ("order_status", "order_tracking"):
            order_num = entities.get("order_number")
            email = entities.get("email")
            if not order_num:
                # ask for order number (and email) to verify
                return jsonify({"reply": "Please provide your order number (and the email used for the order) so I can look it up."})
            order = find_order(order_num, email)
            if not order:
                return jsonify({"reply": "I couldn't find that order. Double-check the order number and email, or type just the order number without '#'. "})
            # format a short reply
            shipping = order.get("fulfillmentStatus") or "Not fulfilled yet"
            total = order.get("totalPriceSet", {}).get("shopMoney", {}).get("amount")
            reply = f"Order {order.get('name')} ({order.get('orderNumber')}) — status: {shipping}. Total: {total}. If you'd like tracking details, reply 'tracking' and I'll fetch more info."
            return jsonify({"reply": reply})

        elif intent == "greeting":
            return jsonify({"reply": "Hi! I'm LayerLabs support — I can help with product details, order status, and tracking. How can I help?"})

        else:
            # fallback: try to answer generically via Gemini
            gen = model.generate_content(user_message)
            return jsonify({"reply": gen.text})

    except requests.HTTPError as e:
        return jsonify({"error": f"Shopify API error: {str(e)}"}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/")
def home():
    return render_template("index.html")
