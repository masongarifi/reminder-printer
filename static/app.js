const form = document.querySelector("#reminder-form");
const message = document.querySelector("#message");
const panel = document.querySelector("#preview-panel");
const receipt = document.querySelector("#receipt");

function payload() {
  return {
    title: document.querySelector("#title").value,
    include_completed: document.querySelector("#include-completed").checked,
    items: document.querySelector("#text").value.split(/\r?\n/)
  };
}

async function send(path) {
  message.className = "";
  message.textContent = "Working…";
  try {
    const response = await fetch(path, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload())
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || `Request failed (${response.status})`);
    return data;
  } catch (error) {
    message.className = "error";
    message.textContent = error.message;
    throw error;
  }
}

document.querySelector("#preview").addEventListener("click", async () => {
  try {
    const data = await send("/api/preview-reminders");
    receipt.textContent = data.receipt;
    panel.hidden = false;
    message.className = "success";
    message.textContent = "Preview ready.";
  } catch (_) {}
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const data = await send("/api/print-reminders");
    message.className = "success";
    message.textContent = data.message;
  } catch (_) {}
});

