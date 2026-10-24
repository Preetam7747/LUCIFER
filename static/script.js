document.addEventListener("DOMContentLoaded", () => {
  // Attach the per-session CSRF token to every ordinary HTML form.
  const token = document.querySelector('meta[name="csrf-token"]')?.content;
  if (token) document.querySelectorAll('form[method="post"], form:not([method])').forEach(form => {
    if (!form.querySelector('input[name="_csrf_token"]')) {
      const input = document.createElement('input');
      input.type = 'hidden'; input.name = '_csrf_token'; input.value = token;
      form.appendChild(input);
    }
  });
  const toggle = document.getElementById("menuToggle");
  const sidebar = document.getElementById("sidebar");
  if (toggle && sidebar) toggle.addEventListener("click", () => sidebar.classList.toggle("open"));
  document.querySelectorAll(".flash-close").forEach(button => {
    button.addEventListener("click", () => button.closest(".flash")?.remove());
  });
  document.querySelectorAll('input[type="datetime-local"]').forEach(input => {
    if (!input.value) {
      const now = new Date();
      now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
      input.min = now.toISOString().slice(0, 16);
    }
  });
});
