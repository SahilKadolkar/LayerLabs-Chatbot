(function () {

  // ============================================================
  // CONFIG — change this when you deploy to Render
  // ============================================================
  const BACKEND_URL = "https://layerlabs-chatbot.onrender.com";
  // For local testing use: "http://localhost:8000"
  // ============================================================

  // ── Styles ───────────────────────────────────────────────────
  // We inject CSS directly into the page via JavaScript
  // This way the widget is self-contained — one file does everything
  const style = document.createElement("style");
  style.innerHTML = `
    #ll-chat-bubble {
      position: fixed;
      bottom: 24px;
      right: 24px;
      width: 56px;
      height: 56px;
      background: #1a1a1a;
      border-radius: 50%;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 4px 16px rgba(0,0,0,0.2);
      z-index: 9999;
      transition: transform 0.2s;
    }

    #ll-chat-bubble:hover {
      transform: scale(1.08);
    }

    #ll-chat-bubble svg {
      width: 26px;
      height: 26px;
      fill: white;
    }

    #ll-chat-window {
      position: fixed;
      bottom: 92px;
      right: 24px;
      width: 340px;
      height: 480px;
      background: #ffffff;
      border-radius: 16px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.15);
      display: none;
      flex-direction: column;
      z-index: 9999;
      font-family: sans-serif;
      overflow: hidden;
    }

    #ll-chat-window.open {
      display: flex;
    }

    #ll-chat-header {
      background: #1a1a1a;
      color: white;
      padding: 16px;
      font-size: 14px;
      font-weight: 600;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    #ll-chat-header span {
      font-size: 18px;
      cursor: pointer;
      opacity: 0.7;
    }

    #ll-chat-header span:hover {
      opacity: 1;
    }

    #ll-chat-messages {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .ll-message {
      max-width: 80%;
      padding: 10px 14px;
      border-radius: 12px;
      font-size: 13px;
      line-height: 1.5;
    }

    .ll-message.bot {
      background: #f1f1f1;
      color: #1a1a1a;
      align-self: flex-start;
      border-bottom-left-radius: 4px;
    }

    .ll-message.user {
      background: #1a1a1a;
      color: white;
      align-self: flex-end;
      border-bottom-right-radius: 4px;
    }

    .ll-message.typing {
      background: #f1f1f1;
      color: #999;
      align-self: flex-start;
      font-style: italic;
    }

    #ll-chat-input-area {
      display: flex;
      padding: 12px;
      border-top: 1px solid #f0f0f0;
      gap: 8px;
    }

    #ll-chat-input {
      flex: 1;
      border: 1px solid #e0e0e0;
      border-radius: 8px;
      padding: 8px 12px;
      font-size: 13px;
      outline: none;
      resize: none;
    }

    #ll-chat-input:focus {
      border-color: #1a1a1a;
    }

    #ll-chat-send {
      background: #1a1a1a;
      color: white;
      border: none;
      border-radius: 8px;
      padding: 8px 14px;
      cursor: pointer;
      font-size: 13px;
      font-weight: 600;
      transition: opacity 0.2s;
    }

    #ll-chat-send:hover {
      opacity: 0.8;
    }

    #ll-chat-send:disabled {
      opacity: 0.4;
      cursor: not-allowed;
    }
  `;
  document.head.appendChild(style);

  // ── HTML Structure ───────────────────────────────────────────
  // The chat bubble button
  const bubble = document.createElement("div");
  bubble.id = "ll-chat-bubble";
  bubble.innerHTML = `
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <path d="M12 2C6.48 2 2 6.48 2 12c0 1.85.5 3.58 1.37 5.06L2 22l4.94-1.37A9.94 9.94 0 0012 22c5.52 0 10-4.48 10-10S17.52 2 12 2zm1 15H7v-2h6v2zm2-4H7v-2h8v2zm0-4H7V7h8v2z"/>
    </svg>
  `;

  // The chat window
  const chatWindow = document.createElement("div");
  chatWindow.id = "ll-chat-window";
  chatWindow.innerHTML = `
    <div id="ll-chat-header">
      <div>💬 LayerLabs Support</div>
      <span id="ll-close-btn">✕</span>
    </div>
    <div id="ll-chat-messages">
      <div class="ll-message bot">
        Hi! 👋 I'm the LayerLabs assistant. Ask me about our products, 
        prices, shipping, or anything else!
      </div>
    </div>
    <div id="ll-chat-input-area">
      <input 
        id="ll-chat-input" 
        type="text" 
        placeholder="Ask something..." 
      />
      <button id="ll-chat-send">Send</button>
    </div>
  `;

  // Add both to the page
  document.body.appendChild(bubble);
  document.body.appendChild(chatWindow);

  // ── References to elements we'll use repeatedly ──────────────
  const messagesDiv = document.getElementById("ll-chat-messages");
  const input = document.getElementById("ll-chat-input");
  const sendBtn = document.getElementById("ll-chat-send");
  const closeBtn = document.getElementById("ll-close-btn");

  // ── Toggle open/close ────────────────────────────────────────
  bubble.addEventListener("click", () => {
    chatWindow.classList.toggle("open");
    if (chatWindow.classList.contains("open")) {
      input.focus();
    }
  });

  closeBtn.addEventListener("click", () => {
    chatWindow.classList.remove("open");
  });

  // ── Helper — add a message bubble to the chat ────────────────
  // type = "user", "bot", or "typing"
  function addMessage(text, type) {
    const msg = document.createElement("div");
    msg.className = `ll-message ${type}`;
    msg.textContent = text;
    messagesDiv.appendChild(msg);

    // Auto scroll to the latest message
    messagesDiv.scrollTop = messagesDiv.scrollHeight;

    return msg;
  }

  // ── Send message to backend ──────────────────────────────────
  async function sendMessage() {
    const question = input.value.trim();

    // Don't send empty messages
    if (!question) return;

    // Show user's message in the chat
    addMessage(question, "user");

    // Clear input and disable send button while waiting
    input.value = "";
    sendBtn.disabled = true;

    // Show typing indicator while waiting for response
    const typingMsg = addMessage("Typing...", "typing");

    try {
      // POST the question to your FastAPI backend
      // The backend runs the RAG chain and returns an answer
      const response = await fetch(`${BACKEND_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question: question }),
      });

      const data = await response.json();

      // Remove typing indicator
      typingMsg.remove();

      // Show the bot's answer
      addMessage(data.answer, "bot");

    } catch (error) {
      // If the backend is down or unreachable
      typingMsg.remove();
      addMessage(
        "Sorry, I'm having trouble connecting. Please try again or visit layerlabs.in directly.",
        "bot"
      );
    }

    // Re-enable send button
    sendBtn.disabled = false;
    input.focus();
  }

  // ── Event listeners for sending ──────────────────────────────
  // Click the send button
  sendBtn.addEventListener("click", sendMessage);

  // Press Enter key (but not Shift+Enter)
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

})();
// The entire widget is wrapped in an IIFE
// (Immediately Invoked Function Expression)
// This means all variables are private to this function
// They won't clash with Shopify's own JavaScript variables