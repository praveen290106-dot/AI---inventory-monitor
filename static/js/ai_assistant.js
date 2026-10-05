/**
 * AI Assistant Chat Controller
 * Communicates strictly with the backend Flask endpoint (/api/ai/chat).
 * Microsoft Foundry keys and credentials are never touched by or exposed to client-side JS.
 */

document.addEventListener("DOMContentLoaded", () => {
  checkFoundryStatus();

  const chatForm = document.getElementById("chatForm");
  chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const input = document.getElementById("userInput");
    const message = input.value.trim();
    if (!message) return;

    input.value = "";
    sendMessage(message);
  });
});

async function checkFoundryStatus() {
  try {
    const res = await fetch("/api/health");
    const data = await res.json();
    const banner = document.getElementById("aiConfigAlert");
    const alertText = document.getElementById("aiConfigAlertText");

    if (!data.microsoft_foundry_configured) {
      banner.style.display = "flex";
      alertText.innerHTML = `
        <strong>Microsoft Foundry configuration is incomplete.</strong>
        AI assistant endpoints require valid <code>FOUNDRY_ENDPOINT</code>, <code>FOUNDRY_API_KEY</code>,
        and <code>FOUNDRY_DEPLOYMENT_NAME</code> in your <code>.env</code> file.
      `;
    } else {
      banner.style.display = "none";
    }
  } catch (e) {
    console.warn("Could not check Foundry health:", e);
  }
}

function sendPrompt(promptText) {
  document.getElementById("userInput").value = promptText;
  sendMessage(promptText);
}

async function sendMessage(message) {
  appendUserMessage(message);

  const sendBtn = document.getElementById("sendBtn");
  const userInput = document.getElementById("userInput");

  sendBtn.disabled = true;
  userInput.disabled = true;

  const loadingBubbleId = appendTypingIndicator();

  try {
    const response = await fetch("/api/ai/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: message })
    });

    const data = await response.json();
    removeTypingIndicator(loadingBubbleId);

    if (response.ok && data.success) {
      appendAssistantMessage(data.response);
    } else {
      const errorMsg = data.error || "Failed to receive response from Microsoft Foundry AI service.";
      appendErrorMessage(errorMsg);
    }
  } catch (err) {
    removeTypingIndicator(loadingBubbleId);
    appendErrorMessage("Network error: Could not reach Flask backend AI service.");
  } finally {
    sendBtn.disabled = false;
    userInput.disabled = false;
    userInput.focus();
  }
}

function appendUserMessage(text) {
  const container = document.getElementById("chatMessages");
  const bubble = document.createElement("div");
  bubble.className = "message-bubble user";
  bubble.innerHTML = `
    <div class="user-avatar" style="width: 32px; height: 32px; font-size: 0.85rem; flex-shrink: 0; background: linear-gradient(135deg, #7e22ce, #a855f7); color: #fff; box-shadow: 0 0 10px rgba(168, 85, 247, 0.4);">
      <i class="fa-solid fa-user"></i>
    </div>
    <div class="message-content">
      <p>${escapeHtml(text)}</p>
    </div>
  `;
  container.appendChild(bubble);
  scrollToBottom();
}

function appendAssistantMessage(text) {
  const container = document.getElementById("chatMessages");
  const bubble = document.createElement("div");
  bubble.className = "message-bubble assistant";
  bubble.innerHTML = `
    <div class="assistant-avatar" style="width: 32px; height: 32px; font-size: 0.9rem; flex-shrink: 0;">
      <i class="fa-solid fa-robot"></i>
    </div>
    <div class="message-content">
      ${formatMarkdown(text)}
    </div>
  `;
  container.appendChild(bubble);
  scrollToBottom();
}

function appendErrorMessage(errorText) {
  const container = document.getElementById("chatMessages");
  const bubble = document.createElement("div");
  bubble.className = "message-bubble assistant";
  bubble.innerHTML = `
    <div class="assistant-avatar" style="width: 32px; height: 32px; font-size: 0.9rem; flex-shrink: 0; background: #dc2626;">
      <i class="fa-solid fa-triangle-exclamation"></i>
    </div>
    <div class="message-content" style="border-color: rgba(239, 68, 68, 0.4); background: rgba(239, 68, 68, 0.08);">
      <p style="color: #f87171; font-weight: 600;">
        <i class="fa-solid fa-circle-xmark"></i> Microsoft Foundry Service Notice:
      </p>
      <p style="margin-top: 6px; font-size: 0.88rem; color: #fecaca; line-height: 1.4;">
        ${escapeHtml(errorText)}
      </p>
    </div>
  `;
  container.appendChild(bubble);
  scrollToBottom();
}

function appendTypingIndicator() {
  const container = document.getElementById("chatMessages");
  const id = "typing-" + Date.now();
  const bubble = document.createElement("div");
  bubble.id = id;
  bubble.className = "message-bubble assistant";
  bubble.innerHTML = `
    <div class="assistant-avatar" style="width: 32px; height: 32px; font-size: 0.9rem; flex-shrink: 0;">
      <i class="fa-solid fa-robot"></i>
    </div>
    <div class="message-content" style="color: var(--text-dim); display: flex; align-items: center; gap: 8px;">
      <i class="fa-solid fa-circle-notch fa-spin" style="color: var(--primary);"></i>
      <span>Analyzing inventory data with Microsoft Foundry...</span>
    </div>
  `;
  container.appendChild(bubble);
  scrollToBottom();
  return id;
}

function removeTypingIndicator(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

function scrollToBottom() {
  const container = document.getElementById("chatMessages");
  container.scrollTop = container.scrollHeight;
}

function clearChat() {
  const container = document.getElementById("chatMessages");
  container.innerHTML = `
    <div class="message-bubble assistant">
      <div class="assistant-avatar" style="width: 32px; height: 32px; font-size: 0.9rem; flex-shrink: 0;">
        <i class="fa-solid fa-robot"></i>
      </div>
      <div class="message-content">
        <p>Chat cleared. Ask me any question regarding your current inventory, stock levels, or replenishment priorities!</p>
      </div>
    </div>
  `;
}

function formatMarkdown(text) {
  if (!text) return "";
  let html = escapeHtml(text);

  // Bold
  html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

  // Headers (### Header)
  html = html.replace(/^### (.*$)/gim, '<h4 style="color:#38bdf8; margin: 10px 0 4px 0;">$1</h4>');
  html = html.replace(/^## (.*$)/gim, '<h3 style="color:#38bdf8; margin: 12px 0 6px 0;">$1</h3>');
  html = html.replace(/^# (.*$)/gim, '<h2 style="color:#38bdf8; margin: 14px 0 8px 0;">$1</h2>');

  // Bullet points
  html = html.replace(/^\* (.*$)/gim, '<li style="margin-left: 20px;">$1</li>');
  html = html.replace(/^- (.*$)/gim, '<li style="margin-left: 20px;">$1</li>');

  // Code inline
  html = html.replace(/`(.*?)`/g, '<code style="background:#1e293b; padding:2px 6px; border-radius:4px; font-family:monospace; color:#38bdf8;">$1</code>');

  // Line breaks
  html = html.replace(/\n\n/g, '<div style="margin-top: 8px;"></div>');
  html = html.replace(/\n/g, "<br>");

  return html;
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}
