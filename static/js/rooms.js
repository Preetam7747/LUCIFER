document.addEventListener("DOMContentLoaded", function () {
    const roomButtons = document.querySelectorAll(".room-action");

    roomButtons.forEach(function (button) {
        button.addEventListener("click", function () {
            const roomNumber = button.dataset.room;

            if (roomNumber) {
                console.log("Room selected:", roomNumber);
            }
        });
    });
});