document.addEventListener("DOMContentLoaded", function () {
    console.log("Smart Hostel Management System loaded.");

    const alerts = document.querySelectorAll(".alert");

    alerts.forEach(function (alert) {
        setTimeout(function () {
            alert.style.opacity = "0";
            alert.style.transition = "opacity 0.5s";

            setTimeout(function () {
                alert.remove();
            }, 500);
        }, 4000);
    });
});