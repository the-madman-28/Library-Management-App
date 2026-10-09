document.addEventListener("DOMContentLoaded", function () {

    const notifications = document.querySelectorAll(
        "[data-notification]"
    );


    notifications.forEach(function (notification) {

        const closeButton = notification.querySelector(
            "[data-notification-close]"
        );


        function closeNotification() {

            if (notification.classList.contains(
                "notification-closing"
            )) {
                return;
            }


            notification.classList.add(
                "notification-closing"
            );


            setTimeout(function () {

                notification.remove();

            }, 200);

        }


        /* =====================================================
           OK BUTTON
        ====================================================== */

        if (closeButton) {

            closeButton.addEventListener(
                "click",
                closeNotification
            );

        }


        /* =====================================================
           CLICK OUTSIDE MODAL
        ====================================================== */

        notification.addEventListener(
            "click",
            function (event) {

                if (
                    event.target === notification
                ) {
                    closeNotification();
                }

            }
        );


        /* =====================================================
           ESCAPE KEY
        ====================================================== */

        document.addEventListener(
            "keydown",
            function (event) {

                if (event.key === "Escape") {

                    closeNotification();

                }

            }
        );


        /* =====================================================
           AUTO CLOSE SUCCESS NOTIFICATIONS
        ====================================================== */

        const category =
            notification.dataset.category;


        if (category === "success") {

            setTimeout(
                closeNotification,
                4000
            );

        }

    });

});