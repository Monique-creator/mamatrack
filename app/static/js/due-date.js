// Shows the follow-up date (delivery + 42 days) as soon as a delivery date is picked.
(function () {
  const input = document.getElementById("delivery_date");
  const preview = document.getElementById("due-preview");
  if (!input || !preview) return;

  function update() {
    if (!input.value) { preview.textContent = ""; return; }
    const due = new Date(input.value + "T00:00:00");
    due.setDate(due.getDate() + 42);
    preview.textContent = "Follow-up visit due on " + due.toLocaleDateString("en-GB",
      { day: "numeric", month: "long", year: "numeric" });
  }

  input.addEventListener("input", update);
  update();
})();