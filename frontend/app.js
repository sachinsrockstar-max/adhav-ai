// ADHAV AI - Stage 5: chat page that saves your conversation in this browser.
// This file talks to our own server at /chat. No API key is here, and none should ever be.

const chatBox = document.getElementById("chat");
const form = document.getElementById("chat-form");
const input = document.getElementById("message-input");
const sendButton = document.getElementById("send-button");
const newChatButton = document.getElementById("new-chat-button");

const MAX_CHARS = 4000;            // Same limit as the backend.
const STORAGE_KEY = "adhav_chat_v1";
const MAX_SAVED_MESSAGES = 200;    // Keeps the saved chat small.
const MAX_SENT_MESSAGES = 40;      // How many earlier messages we send along.
const GREETING = "Heyy 😌 What's up?";

// The conversation: a list of {role: "user" or "assistant", content: "text"}.
let messages = [];
let isWaiting = false;
let typingElement = null;

// ---------------------------------------------------------------------------
// Saving and loading (localStorage)
// ---------------------------------------------------------------------------

function loadMessages() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return [];
    }
    const data = JSON.parse(raw);
    if (!Array.isArray(data)) {
      return [];
    }
    // Keep only well-formed messages, in case the saved data was damaged.
    return data
      .filter(function (item) {
        return (
          item &&
          (item.role === "user" || item.role === "assistant") &&
          typeof item.content === "string" &&
          item.content.length > 0
        );
      })
      .map(function (item) {
        return { role: item.role, content: item.content };
      });
  } catch (error) {
    return [];
  }
}

function saveMessages() {
  try {
    messages = messages.slice(-MAX_SAVED_MESSAGES);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
  } catch (error) {
    // Storage may be blocked or full. The chat still works, it just won't be saved.
  }
}

function clearSavedMessages() {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch (error) {
    // Nothing to do.
  }
}

// ---------------------------------------------------------------------------
// Showing messages
// ---------------------------------------------------------------------------

function scrollToBottom() {
  chatBox.scrollTop = chatBox.scrollHeight;
}

// Add a message bubble. We use textContent (not innerHTML) so text can never run as code.
function addMessage(role, text, isError) {
  const bubble = document.createElement("div");
  bubble.className = "message " + role + (isError ? " error" : "");
  bubble.textContent = text;
  chatBox.appendChild(bubble);
  scrollToBottom();
}

// Draw the whole saved conversation (or the greeting if there is none).
function renderAll() {
  chatBox.innerHTML = "";
  if (messages.length === 0) {
    addMessage("adhav", GREETING, false);
    return;
  }
  messages.forEach(function (item) {
    addMessage(item.role === "user" ? "user" : "adhav", item.content, false);
  });
}

function showTyping() {
  typingElement = document.createElement("div");
  typingElement.className = "message adhav typing";
  typingElement.innerHTML = "<span></span><span></span><span></span>";
  chatBox.appendChild(typingElement);
  scrollToBottom();
}

function hideTyping() {
  if (typingElement) {
    typingElement.remove();
    typingElement = null;
  }
}

function setWaiting(waiting) {
  isWaiting = waiting;
  sendButton.disabled = waiting;
  newChatButton.disabled = waiting;
}

// Make the text box grow as you type (up to a limit set in CSS).
function autoResize() {
  input.style.height = "auto";
  input.style.height = input.scrollHeight + "px";
}

// ---------------------------------------------------------------------------
// Sending a message
// ---------------------------------------------------------------------------

async function sendMessage() {
  const text = input.value.trim();

  if (!text || isWaiting) {
    return;
  }

  if (text.length > MAX_CHARS) {
    addMessage("adhav", "That's a long one! Please keep it under " + MAX_CHARS + " characters.", true);
    return;
  }

  // If this is the very first message, the greeting bubble stays on screen.
  addMessage("user", text);
  input.value = "";
  autoResize();
  setWaiting(true);
  showTyping();

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: text,
        history: messages.slice(-MAX_SENT_MESSAGES),
      }),
    });

    let data = null;
    try {
      data = await response.json();
    } catch (parseError) {
      data = null;
    }

    if (!response.ok) {
      let detail = "Something went wrong. Please try again.";
      if (data && typeof data.detail === "string") {
        detail = data.detail;
      }
      throw new Error(detail);
    }

    // Success: save this exchange, then show the reply.
    messages.push({ role: "user", content: text });
    messages.push({ role: "assistant", content: data.reply });
    saveMessages();

    hideTyping();
    addMessage("adhav", data.reply, false);
  } catch (error) {
    hideTyping();
    if (error instanceof TypeError) {
      addMessage("adhav", "I can't reach the server. Is it still running in your terminal?", true);
    } else {
      addMessage("adhav", error.message, true);
    }
  } finally {
    hideTyping();
    setWaiting(false);
    input.focus();
  }
}

// ---------------------------------------------------------------------------
// Buttons and keys
// ---------------------------------------------------------------------------

form.addEventListener("submit", function (event) {
  event.preventDefault();
  sendMessage();
});

// Enter sends. Shift+Enter makes a new line.
// event.isComposing keeps Tamil/IME typing from sending too early.
input.addEventListener("keydown", function (event) {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    sendMessage();
  }
});

input.addEventListener("input", autoResize);

newChatButton.addEventListener("click", function () {
  if (isWaiting) {
    return;
  }
  if (messages.length === 0) {
    input.focus();
    return;
  }
  const sure = window.confirm("Start a new chat? This clears the current conversation on this device.");
  if (!sure) {
    return;
  }
  messages = [];
  clearSavedMessages();
  renderAll();
  input.focus();
});

// ---------------------------------------------------------------------------
// Start
// ---------------------------------------------------------------------------

messages = loadMessages();
renderAll();
input.focus();