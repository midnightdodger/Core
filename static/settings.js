(() => {
    const closeButton = document.getElementById("settings-close");
    if (!closeButton) {
        return;
    }

    closeButton.addEventListener("click", () => {
        const parentDoc = window.parent?.document;
        if (!parentDoc) {
            return;
        }
        const webview = parentDoc.getElementById("webview");
        if (!webview) {
            return;
        }
        webview.style.maxHeight = "0px";
        webview.style.opacity = "0";
        webview.addEventListener(
            "transitionend",
            () => {
                if (webview.style.maxHeight === "0px") {
                    webview.classList.add("hidden");
                }
            },
            { once: true }
        );
    });

    const refreshForm = document.querySelector("form[data-refresh-parent]");
    if (refreshForm) {
        refreshForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            try {
                await fetch(refreshForm.action, {
                    method: refreshForm.method || "POST",
                    body: new FormData(refreshForm),
                });
            } catch (error) {
                // If logout fails, still try to refresh the parent view.
            }
            if (window.parent) {
                window.parent.location.href = "/";
            }
        });
    }
})();
