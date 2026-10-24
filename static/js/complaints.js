document.addEventListener("DOMContentLoaded", function () {
    const complaintForm = document.getElementById("complaintForm");

    if (complaintForm) {
        complaintForm.addEventListener("submit", function () {
            const button = complaintForm.querySelector("button[type='submit']");

            if (button) {
                button.disabled = true;
                button.textContent = "Submitting...";
            }
        });
    }

    const deleteButtons = document.querySelectorAll(".delete-complaint");

    deleteButtons.forEach(function (button) {
        button.addEventListener("click", function (event) {
            if (!confirm("Are you sure you want to delete this complaint?")) {
                event.preventDefault();
            }
        });
    });
});