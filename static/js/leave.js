document.addEventListener("DOMContentLoaded", function () {
    const leaveForm = document.getElementById("leaveForm");

    if (leaveForm) {
        leaveForm.addEventListener("submit", function () {
            const button = leaveForm.querySelector("button[type='submit']");

            if (button) {
                button.disabled = true;
                button.textContent = "Submitting...";
            }
        });
    }
});