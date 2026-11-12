(function () {
  const userId = document.getElementById("net-status").dataset.user;
  const KEY = "mamatrack-queue-" + userId;
  const KEEP_DAYS = 14;
  const dialog = document.getElementById("visit-dialog");
  const form = document.getElementById("visit-form");
  const STATE_TEXT = {
    pending: "Pending sync",
    synced: "Synced",
    merged: "Synced (combined)",
    review: "Sent for nurse review",
    rejected: "Not accepted",
  };

  function load() {
    try { return JSON.parse(localStorage.getItem(KEY)) || []; } catch (e) { return []; }
  }

  function save(queue) {
    const cutoff = Date.now() - KEEP_DAYS * 864e5;
    const kept = queue.filter((u) => u.state === "pending" || Date.parse(u.recorded_at) > cutoff);
    try { localStorage.setItem(KEY, JSON.stringify(kept)); } catch (e) { /* storage full or blocked */ }
  }

  function esc(text) {
    const div = document.createElement("div");
    div.textContent = text == null ? "" : String(text);
    return div.innerHTML;
  }

  function newRef() {
    if (window.crypto && crypto.randomUUID) return crypto.randomUUID();
    return Date.now().toString(36) + Math.random().toString(36).slice(2);
  }

  function render(note) {
    const queue = load();
    const banner = document.getElementById("net-status");
    banner.className = "net " + (navigator.onLine ? "net-on" : "net-off");
    banner.textContent = note || (navigator.onLine
      ? "Online · updates go straight to the health centre"
      : "Offline · updates are kept on this phone until the network is back");

    document.getElementById("queue").hidden = queue.length === 0;
    document.getElementById("queue-list").innerHTML = queue.slice().reverse().map((u) =>
      `<li class="q-${u.state}"><strong>${esc(u.name)}</strong> · ${esc(u.visit_date)} · ${esc(u.outcome)}
       <span>${STATE_TEXT[u.state] || ""}${u.message ? " · " + esc(u.message) : ""}</span></li>`).join("");

    queue.filter((u) => u.state !== "rejected").forEach((u) => {
      const button = document.querySelector(`.open-form[data-id="${u.mother_id}"]`);
      if (!button) return;
      button.disabled = true;
      button.textContent = u.state === "pending" ? "Saved on this phone · waiting to sync" : "Visit synced";
    });
  }

  let syncing = false;

  async function sync() {
    const queue = load();
    const pending = queue.filter((u) => u.state === "pending");
    if (syncing || !pending.length || !navigator.onLine) return render();
    syncing = true;

    try {
      const res = await fetch("/api/sync", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ updates: pending }),
      });
      if (res.status === 401) return render("Signed out · sign in again to send pending updates");
      const data = await res.json();
      data.results.forEach((r) => {
        const item = queue.find((u) => u.ref === r.ref);
        if (item) Object.assign(item, { state: r.result, message: r.message });
      });
      save(queue);
      render();
    } catch (e) {
      render("Network is unstable · will retry automatically");
    } finally {
      syncing = false;
    }
  }

  document.querySelectorAll(".open-form").forEach((btn) => {
    btn.addEventListener("click", () => {
      form.reset();
      form.mother_id.value = btn.dataset.id;
      form.visit_date.min = btn.dataset.delivered;
      form.visit_date.value = form.visit_date.max;
      form.dataset.name = btn.dataset.name;
      document.getElementById("dialog-title").textContent = "Log visit · " + btn.dataset.name;
      document.getElementById("form-error").textContent = "";
      dialog.showModal();
    });
  });

  document.getElementById("save-visit").addEventListener("click", (event) => {
    const date = form.visit_date.value;
    const outcome = form.querySelector("[name=outcome]:checked");
    let error = "";
    if (!date || date > form.visit_date.max) error = "Pick a visit date that is not in the future.";
    else if (date < form.visit_date.min) error = "Visit date cannot be before the delivery date.";
    else if (!outcome) error = "Choose an outcome.";

    if (error) {
      event.preventDefault();
      document.getElementById("form-error").textContent = error;
      return;
    }

    const queue = load();
    queue.push({
      ref: newRef(),
      user_id: userId,
      mother_id: Number(form.mother_id.value),
      name: form.dataset.name,
      visit_date: date,
      outcome: outcome.value,
      note: form.note.value,
      risk_type: form.risk_type.value,
      risk_note: form.note.value,
      recorded_at: new Date().toISOString(),
      state: "pending",
    });
    save(queue);
    render();
    sync();
  });

  document.getElementById("sync-now").addEventListener("click", sync);
  window.addEventListener("online", () => { render(); setTimeout(sync, 1000); });
  window.addEventListener("offline", () => render());
  setInterval(sync, 15000);

  if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js");
  render();
  sync();
})();