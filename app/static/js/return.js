
document.addEventListener("DOMContentLoaded", function () {
    const config = document.getElementById("returnConfig");

    if (!config) return;

    const searchUrl = config.dataset.searchUrl;
    const isbnUrl = config.dataset.isbnUrl;

    const searchInput = document.getElementById("returnSearch");
    const scanButton = document.getElementById("scanButton");
    const stopScannerButton = document.getElementById("stopScannerButton");
    const scannerPanel = document.getElementById("scannerPanel");
    const liveStatus = document.getElementById("liveStatus");
    const searchSpinner = document.getElementById("searchSpinner");

    const resultsSection = document.getElementById("resultsSection");
    const resultsContainer = document.getElementById("resultsContainer");

    const selectedBooks = document.getElementById("selectedBooks");
    const selectedCount = document.getElementById("selectedCount");
    const selectedInputs = document.getElementById("selectedInputs");
    const returnForm = document.getElementById("returnForm");
    const returnSubmitButton = document.getElementById("returnSubmitButton");
    const clearSelectionButton = document.getElementById("clearSelectionButton");

    const returnConfirmation = document.getElementById("returnConfirmation");
    const confirmationText = document.getElementById("confirmationText");
    const confirmReturnButton = document.getElementById("confirmReturnButton");
    const cancelReturnButton = document.getElementById("cancelReturnButton");

    const selectedLoans = new Map();

    let searchTimer = null;
    let activeSearchController = null;
    let scanner = null;
    let scannerRunning = false;
    let isbnBusy = false;
    let returnConfirmed = false;
    let submittingReturn = false;

    function escapeHtml(value) {
        return String(value ?? "").replace(/[&<>"']/g, function (char) {
            return {
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;",
                "'": "&#39;"
            }[char];
        });
    }

    function status(message, type = "info") {
        liveStatus.replaceChildren();

        if (!message) return;

        const classes = {
            info: "text-primary",
            success: "text-success",
            warning: "text-warning",
            error: "text-danger"
        };

        const span = document.createElement("span");
        span.className = classes[type] || classes.info;
        span.textContent = message;
        liveStatus.appendChild(span);
    }

    function normalizeLoan(item) {
        return {
            transaction_id: String(item.transaction_id ?? item.id ?? ""),
            book_id: item.book_id ?? "",
            book_code: item.book_code ?? "",
            book_title: item.book_title ?? item.title ?? "",
            isbn: item.isbn ?? "",
            employee_id: item.employee_id ?? "",
            employee_code: item.employee_code ?? "",
            employee_name: item.employee_name ?? "",
            issue_date: item.issue_date ?? "",
            due_date: item.due_date ?? ""
        };
    }

    function hideConfirmation() {
        returnConfirmation.hidden = true;
        returnConfirmed = false;
        confirmReturnButton.disabled = false;
        cancelReturnButton.disabled = false;
        confirmReturnButton.textContent = "Yes, Return Books";
    }

    function renderSelected() {
        const loans = Array.from(selectedLoans.values());

        selectedCount.textContent = loans.length + " selected";
        selectedBooks.replaceChildren();
        selectedInputs.replaceChildren();

        if (loans.length === 0) {
            const emptyMessage = document.createElement("p");
            emptyMessage.className = "return-muted mb-0";
            emptyMessage.textContent = "No books selected yet.";
            selectedBooks.appendChild(emptyMessage);

            returnForm.hidden = true;
            hideConfirmation();
            return;
        }

        loans.forEach(function (loan) {
            const row = document.createElement("div");
            row.className = "selected-row d-flex justify-content-between gap-3";

            const details = document.createElement("div");
            details.innerHTML = `
                <div class="fw-semibold">
                    ${escapeHtml(loan.book_title || "Untitled Book")}
                </div>
                <div class="small return-muted">
                    Book Code: ${escapeHtml(loan.book_code || "N/A")}
                    ${loan.isbn ? " | ISBN: " + escapeHtml(loan.isbn) : ""}
                </div>
                <div class="small">
                    ${escapeHtml(loan.employee_name || "Unknown")}
                    (${escapeHtml(loan.employee_code || "N/A")})
                </div>
            `;

            const removeButton = document.createElement("button");
            removeButton.type = "button";
            removeButton.className = "btn btn-sm btn-outline-danger";
            removeButton.textContent = "Remove";

            removeButton.addEventListener("click", function () {
                selectedLoans.delete(loan.transaction_id);
                hideConfirmation();
                renderSelected();
                syncCheckboxes();
            });

            row.appendChild(details);
            row.appendChild(removeButton);
            selectedBooks.appendChild(row);

            const hidden = document.createElement("input");
            hidden.type = "hidden";
            hidden.name = "transaction_ids";
            hidden.value = loan.transaction_id;
            selectedInputs.appendChild(hidden);
        });

        returnForm.hidden = false;
        returnSubmitButton.disabled = submittingReturn;
    }

    function syncCheckboxes() {
        document.querySelectorAll(".loan-checkbox").forEach(function (checkbox) {
            checkbox.checked = selectedLoans.has(checkbox.value);
        });
    }

    function renderLoans(rawLoans) {
        resultsSection.hidden = false;
        resultsContainer.replaceChildren();

        if (!Array.isArray(rawLoans) || rawLoans.length === 0) {
            const empty = document.createElement("p");
            empty.className = "return-muted border rounded p-3";
            empty.textContent = "No active issued books found.";
            resultsContainer.appendChild(empty);
            return;
        }

        rawLoans.forEach(function (item) {
            const loan = normalizeLoan(item);

            if (!loan.transaction_id) return;

            const row = document.createElement("label");
            row.className = "loan-row";

            const checkbox = document.createElement("input");
            checkbox.type = "checkbox";
            checkbox.className = "form-check-input loan-checkbox";
            checkbox.value = loan.transaction_id;
            checkbox.checked = selectedLoans.has(loan.transaction_id);

            checkbox.addEventListener("change", function () {
                if (checkbox.checked) {
                    selectedLoans.set(loan.transaction_id, loan);
                } else {
                    selectedLoans.delete(loan.transaction_id);
                }

                hideConfirmation();
                renderSelected();
                syncCheckboxes();
            });

            const details = document.createElement("div");
            details.className = "loan-details";

            details.innerHTML = `
                <div class="fw-semibold">
                    ${escapeHtml(loan.book_title || "Untitled Book")}
                </div>
                <div class="small return-muted">
                    Book Code: ${escapeHtml(loan.book_code || "N/A")}
                    ${loan.isbn ? " | ISBN: " + escapeHtml(loan.isbn) : ""}
                </div>
                <div class="small">
                    Employee: ${escapeHtml(loan.employee_name || "Unknown")}
                    (${escapeHtml(loan.employee_code || "N/A")})
                </div>
                <div class="small return-muted">
                    Issued: ${escapeHtml(loan.issue_date || "N/A")}
                    | Due: ${escapeHtml(loan.due_date || "N/A")}
                </div>
            `;

            row.appendChild(checkbox);
            row.appendChild(details);
            resultsContainer.appendChild(row);
        });
    }

    async function searchLoans(query) {
        const term = query.trim();

        if (activeSearchController) {
            activeSearchController.abort();
            activeSearchController = null;
        }

        if (term.length < 2) {
            resultsSection.hidden = true;
            resultsContainer.replaceChildren();
            searchSpinner.classList.remove("active");
            status("");
            return;
        }

        const controller = new AbortController();
        activeSearchController = controller;

        searchSpinner.classList.add("active");
        status("Searching...");

        try {
            const response = await fetch(
                searchUrl + "?q=" + encodeURIComponent(term),
                {
                    method: "GET",
                    headers: { "Accept": "application/json" },
                    signal: controller.signal
                }
            );

            const data = await response.json();

            if (controller.signal.aborted) return;

            if (!response.ok || data.ok === false) {
                throw new Error(data.message || "Search failed.");
            }

            const matches = data.matches || [];
            renderLoans(matches);

            status(
                matches.length
                    ? matches.length + " active loan(s) found."
                    : "No active issued books found.",
                matches.length ? "success" : "warning"
            );
        } catch (error) {
            if (error.name !== "AbortError") {
                status(error.message || "Search failed. Please try again.", "error");
            }
        } finally {
            if (activeSearchController === controller) {
                activeSearchController = null;
                searchSpinner.classList.remove("active");
            }
        }
    }

    searchInput.addEventListener("input", function () {
        clearTimeout(searchTimer);

        if (activeSearchController) {
            activeSearchController.abort();
            activeSearchController = null;
        }

        searchSpinner.classList.remove("active");

        const query = searchInput.value.trim();

        if (query.length < 2) {
            resultsSection.hidden = true;
            resultsContainer.replaceChildren();
            status("");
            return;
        }

        searchTimer = setTimeout(function () {
            searchLoans(query);
        }, 120);
    });

    async function lookupISBN(value) {
        const isbn = String(value || "").trim();

        if (!isbn || isbnBusy) return;

        clearTimeout(searchTimer);

        if (activeSearchController) {
            activeSearchController.abort();
            activeSearchController = null;
        }

        isbnBusy = true;
        scanButton.disabled = true;
        status("Checking ISBN...");

        try {
            const response = await fetch(isbnUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                body: JSON.stringify({ isbn: isbn })
            });

            const data = await response.json();

            if (!response.ok || data.ok === false) {
                throw new Error(data.message || "No active loan found for this ISBN.");
            }

            const matches = data.matches || [];
            renderLoans(matches);

            status(
                matches.length
                    ? "ISBN matched. Select the book(s) to return."
                    : "No active loan found for this ISBN.",
                matches.length ? "success" : "warning"
            );
        } catch (error) {
            status(error.message || "ISBN lookup failed.", "error");
        } finally {
            isbnBusy = false;
            scanButton.disabled = false;
        }
    }

    searchInput.addEventListener("keydown", function (event) {
        if (event.key === "Enter") {
            event.preventDefault();
            lookupISBN(searchInput.value);
        }
    });

    clearSelectionButton.addEventListener("click", function () {
        selectedLoans.clear();
        hideConfirmation();
        renderSelected();
        syncCheckboxes();
    });

    returnForm.addEventListener("submit", function (event) {
        if (returnConfirmed) return;

        event.preventDefault();

        if (selectedLoans.size === 0) {
            status("Select at least one book before returning.", "warning");
            return;
        }

        confirmationText.textContent =
            "Are you sure you want to return " +
            selectedLoans.size +
            " selected book(s)?";

        returnConfirmation.hidden = false;
        returnConfirmation.scrollIntoView({
            behavior: "smooth",
            block: "nearest"
        });
    });

    confirmReturnButton.addEventListener("click", function () {
        if (submittingReturn || selectedLoans.size === 0) return;

        submittingReturn = true;
        returnConfirmed = true;

        confirmReturnButton.disabled = true;
        cancelReturnButton.disabled = true;
        returnSubmitButton.disabled = true;
        confirmReturnButton.textContent = "Returning...";

        returnForm.requestSubmit();
    });

    cancelReturnButton.addEventListener("click", function () {
        hideConfirmation();
    });

    async function stopCamera() {
        if (scanner && scannerRunning) {
            try {
                await scanner.stop();
            } catch (error) {
                // Camera may already have stopped.
            }

            try {
                await scanner.clear();
            } catch (error) {
                // Ignore cleanup errors.
            }
        }

        scanner = null;
        scannerRunning = false;
        scannerPanel.style.display = "none";
    }

    scanButton.addEventListener("click", async function () {
        if (scannerRunning) {
            await stopCamera();
            return;
        }

        if (typeof Html5Qrcode === "undefined") {
            status(
                "Camera library did not load. You can enter the ISBN and press Enter.",
                "error"
            );
            return;
        }

        scannerPanel.style.display = "block";
        scanButton.disabled = true;

        try {
            scanner = new Html5Qrcode("reader");

            await scanner.start(
                { facingMode: "environment" },
                {
                    fps: 12,
                    qrbox: { width: 220, height: 100 },
                    aspectRatio: 1.777
                },
                async function (decodedText) {
                    searchInput.value = decodedText;
                    await stopCamera();
                    await lookupISBN(decodedText);
                },
                function () {
                    // Ignore frames without a detected barcode.
                }
            );

            scannerRunning = true;
            status("Camera is ready. Point it at the ISBN barcode.");
        } catch (error) {
            scanner = null;
            scannerRunning = false;
            scannerPanel.style.display = "none";

            status(
                "Camera could not start. Allow camera access and use localhost or HTTPS.",
                "error"
            );
        } finally {
            scanButton.disabled = false;
        }
    });

    stopScannerButton.addEventListener("click", stopCamera);

    renderSelected();
});
