document.addEventListener(
    "DOMContentLoaded",
    () => {

        const form =
            document.getElementById(
                "comic-form"
            );

        const button =
            document.getElementById(
                "generate-button"
            );

        if (!form || !button) {
            return;
        }


        form.addEventListener(
            "submit",
            () => {

                button.classList.add(
                    "loading"
                );

                button.innerHTML =
                    `
                    <span>
                        ✨ Creating your comic...
                    </span>

                    <span>
                        ⏳
                    </span>
                    `;

            }
        );

    }
);