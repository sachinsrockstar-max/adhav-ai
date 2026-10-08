// ADHAV AI - Stage 6: the Memory panel (view, add, edit, delete, turn on/off).
// It only talks to our own server. No keys are here.
// Everything is wrapped in a function so its names never clash with app.js.

(function () {
  "use strict";

  const memoryButton = document.getElementById("memory-button");
  const overlay = document.getElementById("memory-overlay");
  const closeButton = document.getElementById("memory-close");
  const toggle = document.getElementById("memory-toggle");
  const stateLabel = document.getElementById("memory-state");
  const memoryForm = document.getElementById("memory-form");
  const memoryInput = document.getElementById("memory-input");
  const addButton = document.getElementById("memory-add");
  const messageBox = document.getElementById("memory-message");
  const memoryList = document.getElementById("memory-list");
  const deleteAllButton = document.getElementById("memory-delete-all");
  const chatInput = document.getElementById("message-input");

  let memoryEnabled = true;

  // -------------------------------------------------------------------------
  // Helpers
  // -------------------------------------------------------------------------

  function showMessage(text, isError) {
    messageBox.textContent = text;
    messageBox.className = "memory-message" + (isError ? " error" : "");
  }

  function showError(error) {
    if (error instanceof TypeError) {
      showMessage("I can't reach the server. Is it still running in your terminal?", true);
    } else {
      showMessage(error.message, true);
    }
  }

  // Send a request to our server and return the JSON answer.
  async function api(path, method, body) {
    const options = { method: method, headers: {} };
    if (body !== undefined) {
      options.headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(body);
    }
    const response = await fetch(path, options);

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
    return data;
  }

  function applyEnabledState() {
    toggle.checked = memoryEnabled;
    stateLabel.textContent = memoryEnabled ? "on" : "off";
    memoryInput.disabled = !memoryEnabled;
    addButton.disabled = !memoryEnabled;
    memoryInput.placeholder = memoryEnabled
      ? "Add something for Adhav to remember..."
      : "Turn memory on to save new things";
  }

  // -------------------------------------------------------------------------
  // Showing the list
  // -------------------------------------------------------------------------

  function renderList(memories) {
    memoryList.innerHTML = "";
    deleteAllButton.hidden = memories.length === 0;

    if (memories.length === 0) {
      const empty = document.createElement("li");
      empty.className = "memory-empty";
      empty.textContent = "Nothing saved yet. Add something above, or type \u201cremember that ...\u201d in the chat.";
      memoryList.appendChild(empty);
      return;
    }

    memories.forEach(function (item) {
      const row = document.createElement("li");
      row.className = "memory-item";

      const body = document.createElement("div");
      body.className = "memory-body";

      const text = document.createElement("div");
      text.className = "memory-text";
      text.textContent = item.memory; // textContent keeps it safe

      const badge = document.createElement("span");
      badge.className = "badge";
      badge.textContent = item.category;

      body.appendChild(text);
      body.appendChild(badge);

      const actions = document.createElement("div");
      actions.className = "memory-actions";

      const editButton = document.createElement("button");
      editButton.type = "button";
      editButton.className = "small-button";
      editButton.textContent = "Edit";
      editButton.addEventListener("click", function () {
        editMemory(item);
      });

      const deleteButton = document.createElement("button");
      deleteButton.type = "button";
      deleteButton.className = "small-button danger";
      deleteButton.textContent = "Delete";
      deleteButton.addEventListener("click", function () {
        deleteMemory(item);
      });

      actions.appendChild(editButton);
      actions.appendChild(deleteButton);

      row.appendChild(body);
      row.appendChild(actions);
      memoryList.appendChild(row);
    });
  }

  async function refresh() {
    const data = await api("/memories", "GET");
    memoryEnabled = data.enabled;
    applyEnabledState();
    renderList(data.memories);
  }

  // -------------------------------------------------------------------------
  // Actions
  // -------------------------------------------------------------------------

  async function editMemory(item) {
    const edited = window.prompt("Edit this memory:", item.memory);
    if (edited === null) {
      return;
    }
    const text = edited.trim();
    if (!text || text === item.memory) {
      return;
    }
    try {
      await api("/memories/" + item.id, "PUT", { memory: text });
      await refresh();
      showMessage("Saved your change.", false);
    } catch (error) {
      showError(error);
    }
  }

  async function deleteMemory(item) {
    if (!window.confirm("Delete this memory?\n\n" + item.memory)) {
      return;
    }
    try {
      await api("/memories/" + item.id, "DELETE");
      await refresh();
      showMessage("Deleted.", false);
    } catch (error) {
      showError(error);
    }
  }

  memoryForm.addEventListener("submit", async function (event) {
    event.preventDefault();
    const text = memoryInput.value.trim();
    if (!text) {
      return;
    }
    try {
      await api("/memories", "POST", { memory: text });
      memoryInput.value = "";
      await refresh();
      showMessage("Saved 💚", false);
    } catch (error) {
      showError(error);
    }
  });

  toggle.addEventListener("change", async function () {
    const wanted = toggle.checked;
    try {
      await api("/memory-settings", "PUT", { enabled: wanted });
      memoryEnabled = wanted;
      applyEnabledState();
      showMessage(
        wanted ? "Memory is on." : "Memory is off. Adhav won't use or save memories.",
        false
      );
    } catch (error) {
      toggle.checked = memoryEnabled; // put the switch back
      showError(error);
    }
  });

  deleteAllButton.addEventListener("click", async function () {
    if (!window.confirm("Delete ALL saved memories? This cannot be undone.")) {
      return;
    }
    try {
      await api("/memories", "DELETE");
      await refresh();
      showMessage("All memories deleted.", false);
    } catch (error) {
      showError(error);
    }
  });

  // -------------------------------------------------------------------------
  // Opening and closing the panel
  // -------------------------------------------------------------------------

  async function openPanel() {
    showMessage("", false);
    overlay.hidden = false;
    try {
      await refresh();
    } catch (error) {
      showError(error);
    }
    if (!memoryInput.disabled) {
      memoryInput.focus();
    }
  }

  function closePanel() {
    overlay.hidden = true;
    chatInput.focus();
  }

  memoryButton.addEventListener("click", openPanel);
  closeButton.addEventListener("click", closePanel);

  // Clicking the dark background (outside the box) also closes it.
  overlay.addEventListener("click", function (event) {
    if (event.target === overlay) {
      closePanel();
    }
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && !overlay.hidden) {
      closePanel();
    }
  });
})();