document.addEventListener("DOMContentLoaded", function () {
    console.log("Smart Hostel Dashboard loaded");

    // Animate dashboard cards
    const cards = document.querySelectorAll(".dashboard-card");

    cards.forEach(function (card) {
        card.addEventListener("mouseenter", function () {
            card.style.transform = "translateY(-4px)";
            card.style.transition = "0.2s ease";
        });

        card.addEventListener("mouseleave", function () {
            card.style.transform = "translateY(0)";
        });
    });

    // Confirm before important dashboard actions
    const confirmButtons = document.querySelectorAll("[data-confirm]");

    confirmButtons.forEach(function (button) {
        button.addEventListener("click", function (event) {
            const message =
                button.getAttribute("data-confirm") ||
                "Are you sure you want to continue?";

            if (!confirm(message)) {
                event.preventDefault();
            }
        });
    });

    // Auto-hide Flask flash messages
    const alerts = document.querySelectorAll(".alert");

    alerts.forEach(function (alert) {
        setTimeout(function () {
            alert.style.opacity = "0";
            alert.style.transition = "opacity 0.5s ease";

            setTimeout(function () {
                alert.remove();
            }, 500);
        }, 4000);
    });
});