document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".btn-hint").forEach((btn) => {
    const hints = JSON.parse(btn.dataset.hints || "[]");
    const list = document.getElementById(btn.dataset.target);
    let index = 0;

    const updateLabel = () => {
      if (index >= hints.length) {
        btn.textContent = "No more hints";
        btn.disabled = true;
        return;
      }
      const nextIsLast = index === hints.length - 1;
      btn.textContent = nextIsLast ? "Show Final Answer" : (index === 0 ? "Get a Hint" : "Get Next Hint");
    };

    if (hints.length === 0) {
      btn.disabled = true;
      btn.textContent = "No hints available";
      return;
    }

    btn.addEventListener("click", () => {
      if (index >= hints.length) return;
      const hint = hints[index];
      const li = document.createElement("li");
      li.textContent = hint.text;
      li.className = hint.is_answer ? "hint answer" : "hint";
      list.appendChild(li);
      index += 1;
      updateLabel();
    });

    updateLabel();
  });
});
