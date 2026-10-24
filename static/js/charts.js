document.addEventListener("DOMContentLoaded", function () {
    const canvas = document.getElementById("hostelChart");

    if (!canvas || typeof Chart === "undefined") {
        return;
    }

    new Chart(canvas, {
        type: "bar",
        data: {
            labels: ["Students", "Rooms", "Available Beds"],
            datasets: [
                {
                    label: "Hostel Statistics",
                    data: [
                        Number(canvas.dataset.students || 0),
                        Number(canvas.dataset.rooms || 0),
                        Number(canvas.dataset.beds || 0)
                    ]
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
});