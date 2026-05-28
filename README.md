# 🛍️ LayerLabs Shopify Chatbot

A Flask-based chatbot that integrates with Shopify to answer product-related queries.  
Deployed on **Render**, this chatbot uses the **Shopify Admin API** and **Gemini API** to fetch product details and provide user-friendly responses.

---

## 📌 Features
- 🤖 Chatbot interface for product Q&A  
- 🛒 Fetches live product details from Shopify store  
- 💬 Natural language queries like:  
  - `Tell me about Wise Owl Mini Planter`  
  - `Do you have planters?`  
- 🚀 Deployed with **Gunicorn** on Render  

---

## 🛠️ Tech Stack
- **Flask** (Python backend)  
- **Gunicorn** (production server)  
- **Flask-CORS** (cross-origin support)  
- **Requests** (API calls)  
- **Google Generative AI (Gemini)** for query handling  
- **Shopify Admin API** for product data  

---

## 📂 Project Structure

Shopify-Chatbot/

│── server.py # Flask app

│── requirements.txt # Dependencies

│── .gitignore # Ignore sensitive files (like .env)

## 🔑 Environment Variables
This project requires the following environment variables:  

- SHOPIFY_API_KEY=your_api_key
- SHOPIFY_PASSWORD=your_api_password
- SHOPIFY_STORE=your_store_name.myshopify.com
- GEMINI_API_KEY=your_gemini_api_key

## 📌 Future Improvements

- Add support for greetings (e.g., "Hello", "Hi")
- Enhance error handling for unknown queries
- Expand to handle order tracking and customer FAQs

## 👨‍💻 Author
**Sahil Kadolkar**  
Built with ❤️ using Flask, Shopify API & Gemini AI  
