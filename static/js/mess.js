document.addEventListener("DOMContentLoaded", function () {
    const messForms = document.querySelectorAll(".mess-form");

    messForms.forEach(function (form) {
        form.addEventListener("submit", function () {
            const button = form.querySelector("button[type='submit']");

            if (button) {
                button.disabled = true;
                button.textContent = "Saving...";
            }
        });
    });
});