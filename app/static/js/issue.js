
document.addEventListener("DOMContentLoaded", function () {
    "use strict";

    const form = document.getElementById("issue_book_form");
    const bookSearch = document.getElementById("issue_book_search");
    const cameraStart = document.getElementById("issue_camera_start");
    const cameraStop = document.getElementById("issue_camera_stop");
    const cameraPanel = document.getElementById("issue_camera_panel");
    const cameraContainer = document.getElementById("issue_isbn_camera");
    const statusElement = document.getElementById("issue_book_status");
    const resultsContainer = document.getElementById("issue_search_results");
    const candidatePanel = document.getElementById("issue_candidate_panel");
    const addBookButton = document.getElementById("issue_add_book");
    const cancelCandidateButton = document.getElementById("issue_cancel_candidate");
    const selectedBooksContainer = document.getElementById("issue_selected_books");
    const selectedBookIdsContainer = document.getElementById("issue_selected_book_ids");
    const selectionCount = document.getElementById("issue_selection_count");
    const clearAllButton = document.getElementById("issue_clear_all_books");
    const selectedEmptyMessage = document.getElementById("issue_selected_empty");
    const employeeSelect = document.getElementById("employee_id");
    const dueDateInput = document.getElementById("due_date");
    const submitButton = document.getElementById("issue_submit_button");

    const today = form.dataset.today;
    const isbnLookupUrl = form.dataset.isbnLookupUrl;
    const MAX_BOOKS = 2;

    let employeeTomSelect = null;
    let scanner = null;
    let pendingBook = null;
    let selectedBooks = [];
    let searchTimer = null;
    let searchRequestNumber = 0;
    let lookupInProgress = false;
    let lastInputAt = 0;
    let inputIntervals = [];
    let lastCameraValue = "";
    let lastCameraTime = 0;
    let submitting = false;

    const booksDataElement = document.getElementById("available-books-data");
    let availableBooks = [];

    try {
        availableBooks = JSON.parse(booksDataElement.textContent);
    } catch (error) {
        console.error("Could not parse available books:", error);
    }

    if (!Array.isArray(availableBooks)) {
        availableBooks = [];
    }

    availableBooks = availableBooks.filter(function (book) {
        return book &&
            book.id !== undefined &&
            Number(book.available_copies) > 0;
    });

    const bookById = new Map(
        availableBooks.map(function (book) {
            return [String(book.id), book];
        })
    );

    // Searchable employee dropdown.
    if (employeeSelect && window.TomSelect) {
        employeeTomSelect = new TomSelect(employeeSelect, {
            create: false,
            allowEmptyOption: true,
            maxOptions: 500,
            searchField: ["text"],
            closeAfterSelect: true,
            plugins: ["clear_button"]
        });
    }

    function setStatus(message, type = "info") {
        statusElement.textContent = message;
        statusElement.className = "issue-book-status " + type;
    }

    function clearResults() {
        resultsContainer.replaceChildren();
        resultsContainer.hidden = true;
    }

    function hideCandidate() {
        pendingBook = null;
        candidatePanel.hidden = true;
        addBookButton.disabled = false;
    }

    function normalize(value) {
        return String(value || "").trim().toLowerCase();
    }

    function isAlreadySelected(book) {
        return selectedBooks.some(function (selected) {
            return String(selected.id) === String(book.id);
        });
    }

    function getBookById(id) {
        return bookById.get(String(id)) || null;
    }

    // Show details before adding a book to the issue list.
    function renderCandidate(book) {
        if (!book || book.id === undefined) {
            hideCandidate();
            setStatus("The book information is incomplete.", "error");
            return;
        }

        if (isAlreadySelected(book)) {
            hideCandidate();
            setStatus("This book has already been added.", "warning");
            return;
        }

        if (selectedBooks.length >= MAX_BOOKS) {
            hideCandidate();
            setStatus(
                "You can add a maximum of two books. Remove a book first to select another.",
                "warning"
            );
            return;
        }

        if (Number(book.available_copies) < 1) {
            hideCandidate();
            setStatus("This book has no available copies.", "error");
            return;
        }

        pendingBook = book;

        document.getElementById("candidate_book_title").textContent =
            book.title || "Untitled book";

        document.getElementById("candidate_book_code").textContent =
            "Book ID: " + book.id +
            " | Book Code: " + (book.book_code || "N/A");

        document.getElementById("candidate_book_isbn").textContent =
            "ISBN: " + (book.isbn || "Not recorded");

        document.getElementById("candidate_book_availability").textContent =
            "Available copies: " + book.available_copies;

        candidatePanel.hidden = false;
        addBookButton.disabled = false;

        setStatus(
            "Book found. Click Add Book to include it in the issue.",
            "success"
        );
    }

    function updateSelectionSummary() {
        selectionCount.textContent =
            selectedBooks.length + " of " + MAX_BOOKS + " books selected";

        clearAllButton.disabled = selectedBooks.length === 0;
        selectedEmptyMessage.hidden = selectedBooks.length > 0;

        if (selectedBooks.length >= MAX_BOOKS) {
            bookSearch.disabled = true;
            cameraStart.disabled = true;
            bookSearch.placeholder = "Maximum of 2 books selected";

            clearResults();
            hideCandidate();
        } else {
            bookSearch.disabled = false;
            cameraStart.disabled = false;
            bookSearch.placeholder = "Type a title, book code or ISBN...";
        }

        renderSelectedBooks();
    }

    function renderSelectedBooks() {
        selectedBooksContainer.replaceChildren();
        selectedBookIdsContainer.replaceChildren();

        selectedEmptyMessage.hidden = selectedBooks.length > 0;

        selectedBooks.forEach(function (book, index) {
            const card = document.createElement("div");
            card.className = "issue-selected-book";

            const icon = document.createElement("div");
            icon.className = "issue-selected-book-icon";
            icon.innerHTML = '<i class="bi bi-book"></i>';

            const info = document.createElement("div");
            info.className = "issue-selected-book-info";

            const number = document.createElement("span");
            number.className = "issue-selected-book-number";
            number.textContent = "Book " + (index + 1);

            const title = document.createElement("h4");
            title.textContent = book.title || "Untitled book";

            const code = document.createElement("p");
            code.textContent = "Book Code: " + (book.book_code || "N/A");

            const isbn = document.createElement("p");
            isbn.textContent = "ISBN: " + (book.isbn || "Not recorded");

            const availability = document.createElement("p");
            availability.textContent =
                "Available copies: " + book.available_copies;

            info.append(number, title, code, isbn, availability);

            const removeButton = document.createElement("button");
            removeButton.type = "button";
            removeButton.className =
                "btn btn-sm btn-light issue-selected-remove";

            removeButton.setAttribute(
                "aria-label",
                "Remove " + (book.title || "book")
            );

            removeButton.title = "Remove book";
            removeButton.innerHTML = '<i class="bi bi-trash"></i>';

            removeButton.addEventListener("click", function () {
                selectedBooks = selectedBooks.filter(function (selected) {
                    return String(selected.id) !== String(book.id);
                });

                updateSelectionSummary();
                setStatus("Book removed from the selection.", "info");
            });

            card.append(icon, info, removeButton);
            selectedBooksContainer.appendChild(card);

            // The hidden ID inputs are submitted with the form.
            const hiddenId = document.createElement("input");
            hiddenId.type = "hidden";
            hiddenId.name = "book_ids";
            hiddenId.value = String(book.id);

            selectedBookIdsContainer.appendChild(hiddenId);
        });
    }

    function addPendingBook() {
        if (!pendingBook) {
            setStatus("Search for and select a book first.", "error");
            return;
        }

        if (selectedBooks.length >= MAX_BOOKS) {
            setStatus("A maximum of two books can be issued at once.", "error");
            return;
        }

        if (isAlreadySelected(pendingBook)) {
            setStatus("This book is already in the selected list.", "error");
            return;
        }

        if (Number(pendingBook.available_copies) < 1) {
            setStatus("This book has no available copies.", "error");
            return;
        }

        selectedBooks.push(pendingBook);

        const addedTitle = pendingBook.title || "Book";

        hideCandidate();
        clearResults();
        bookSearch.value = "";

        updateSelectionSummary();

        if (selectedBooks.length < MAX_BOOKS) {
            setStatus(
                '"' + addedTitle + '" added. You can select one more book.',
                "success"
            );
            bookSearch.focus();
        } else {
            setStatus(
                "Both books are selected. Review them before submitting.",
                "success"
            );
        }
    }

    addBookButton.addEventListener("click", addPendingBook);

    cancelCandidateButton.addEventListener("click", function () {
        hideCandidate();
        setStatus(
            "Select another book or continue with your selection.",
            "info"
        );
    });

    clearAllButton.addEventListener("click", function () {
        selectedBooks = [];

        hideCandidate();
        clearResults();
        bookSearch.value = "";

        updateSelectionSummary();

        setStatus("All selected books have been removed.", "info");
        bookSearch.focus();
    });

    /*
     * LIVE SEARCH
     * Searches the available books data supplied by Flask.
     */
    function searchBooks() {
        if (selectedBooks.length >= MAX_BOOKS) {
            clearResults();
            hideCandidate();
            return;
        }

        const query = normalize(bookSearch.value);
        const requestNumber = ++searchRequestNumber;

        clearResults();
        hideCandidate();

        if (!query) {
            setStatus(
                selectedBooks.length
                    ? "Search for another book, or submit the selected books."
                    : "Enter a title, book code or ISBN to search.",
                "info"
            );
            return;
        }

        const selectedIds = new Set(
            selectedBooks.map(function (book) {
                return String(book.id);
            })
        );

        const matches = availableBooks
            .filter(function (book) {
                if (selectedIds.has(String(book.id))) {
                    return false;
                }

                return [
                    book.title,
                    book.book_code,
                    book.isbn,
                    String(book.id)
                ].some(function (value) {
                    return normalize(value).includes(query);
                });
            })
            .sort(function (a, b) {
                function rank(book) {
                    const fields = [
                        book.title,
                        book.book_code,
                        book.isbn,
                        String(book.id)
                    ].map(normalize);

                    return fields.some(function (field) {
                        return field.startsWith(query);
                    }) ? 0 : 1;
                }

                const rankDifference = rank(a) - rank(b);

                if (rankDifference !== 0) {
                    return rankDifference;
                }

                return String(a.title || "").localeCompare(
                    String(b.title || "")
                );
            })
            .slice(0, 30);

        if (requestNumber !== searchRequestNumber) {
            return;
        }

        if (matches.length === 0) {
            setStatus("No available books matched your search.", "info");
            return;
        }

        matches.forEach(function (book) {
            const button = document.createElement("button");
            button.type = "button";
            button.className = "issue-search-result";
            button.setAttribute("role", "option");
            button.setAttribute("aria-selected", "false");

            const title = document.createElement("span");
            title.className = "issue-search-result-title";
            title.textContent = book.title || "Untitled book";

            const meta = document.createElement("span");
            meta.className = "issue-search-result-meta";
            meta.textContent =
                "Book ID: " + book.id +
                " | Code: " + (book.book_code || "N/A") +
                " | ISBN: " + (book.isbn || "N/A") +
                " | Available: " + book.available_copies;

            button.append(title, meta);

            button.addEventListener("click", function () {
                resultsContainer
                    .querySelectorAll(".issue-search-result")
                    .forEach(function (result) {
                        result.classList.remove("active");
                        result.setAttribute("aria-selected", "false");
                    });

                button.classList.add("active");
                button.setAttribute("aria-selected", "true");

                renderCandidate(book);
            });

            resultsContainer.appendChild(button);
        });

        resultsContainer.hidden = false;

        setStatus(
            matches.length +
                " matching book(s). Select one, then click Add Book.",
            "info"
        );
    }

    // Automatically search while typing.
    bookSearch.addEventListener("input", function () {
        if (selectedBooks.length >= MAX_BOOKS) {
            return;
        }

        clearTimeout(searchTimer);

        const now = performance.now();

        if (lastInputAt > 0) {
            const delta = now - lastInputAt;

            if (delta > 0 && delta < 100) {
                inputIntervals.push(delta);

                if (inputIntervals.length > 30) {
                    inputIntervals.shift();
                }
            }
        }

        lastInputAt = now;
        searchTimer = setTimeout(searchBooks, 180);
    });

    /*
     * SOUND FEEDBACK AFTER BARCODE DETECTION
     */
    function beep() {
        try {
            const AudioClass =
                window.AudioContext || window.webkitAudioContext;

            if (!AudioClass) {
                return;
            }

            const context = new AudioClass();

            const playBeep = function () {
                const oscillator = context.createOscillator();
                const gain = context.createGain();

                oscillator.type = "sine";
                oscillator.frequency.value = 900;
                gain.gain.value = 0.12;

                oscillator.connect(gain);
                gain.connect(context.destination);

                oscillator.onended = function () {
                    context.close().catch(function () {});
                };

                oscillator.start();
                oscillator.stop(context.currentTime + 0.13);
            };

            if (context.state === "suspended") {
                context.resume()
                    .then(playBeep)
                    .catch(function () {
                        context.close().catch(function () {});
                    });
            } else {
                playBeep();
            }
        } catch (error) {
            // Sound feedback is optional.
        }
    }

    /*
     * ISBN LOOKUP USING THE EXISTING FLASK ENDPOINT
     */
    async function lookupScannedISBN(rawISBN) {
        const isbn = String(rawISBN || "").trim();

        if (!isbn || lookupInProgress) {
            return;
        }

        if (selectedBooks.length >= MAX_BOOKS) {
            setStatus("You have already selected two books.", "warning");
            return;
        }

        lookupInProgress = true;
        cameraStart.disabled = true;

        clearTimeout(searchTimer);
        clearResults();
        hideCandidate();

        setStatus("Barcode captured. Looking up book...", "info");

        try {
            const response = await fetch(isbnLookupUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                body: JSON.stringify({ isbn: isbn })
            });

            const data = await response.json().catch(function () {
                return {};
            });

            if (!response.ok || data.ok === false || !data.book) {
                setStatus(
                    data.message ||
                    data.error ||
                    "No available book matched this barcode.",
                    "error"
                );
                return;
            }

            const result = data.book;
            const localBook = getBookById(result.id);

            const resolvedBook = {
                id: result.id,
                title: result.title ||
                    (localBook && localBook.title) || "",
                book_code: result.book_code ||
                    (localBook && localBook.book_code) || "",
                isbn: result.isbn ||
                    (localBook && localBook.isbn) || isbn,
                available_copies: result.available_copies !== undefined
                    ? result.available_copies
                    : (localBook ? localBook.available_copies : 0)
            };

            if (
                resolvedBook.id === undefined ||
                resolvedBook.id === null
            ) {
                setStatus(
                    "The ISBN lookup response did not include the book ID.",
                    "error"
                );
                return;
            }

            if (Number(resolvedBook.available_copies) < 1) {
                setStatus("This book has no available copies.", "error");
                return;
            }

            renderCandidate(resolvedBook);

        } catch (error) {
            console.error("ISBN lookup failed:", error);

            setStatus(
                "Could not look up the barcode. Check the server and try again.",
                "error"
            );

        } finally {
            lookupInProgress = false;
            cameraStart.disabled = selectedBooks.length >= MAX_BOOKS;
        }
    }

    /*
     * USB BARCODE SCANNER
     * Most USB scanners type the ISBN and finish with Enter.
     */
    bookSearch.addEventListener("keydown", function (event) {
        if (event.key !== "Enter") {
            return;
        }

        event.preventDefault();
        clearTimeout(searchTimer);

        const value = bookSearch.value.trim();
        const digitsOnly = value.replace(/[\s-]/g, "");

        const recentIntervals = inputIntervals.slice(-10);

        const averageInterval = recentIntervals.length
            ? recentIntervals.reduce(function (sum, value) {
                return sum + value;
            }, 0) / recentIntervals.length
            : Infinity;

        const looksLikeScanner =
            /^\d{8,14}$/.test(digitsOnly) &&
            recentIntervals.length >= 5 &&
            averageInterval < 35;

        inputIntervals = [];
        lastInputAt = 0;

        if (looksLikeScanner) {
            lookupScannedISBN(value);
        } else {
            searchBooks();
        }
    });

    /*
     * STOP CAMERA AND CLEAN UP
     */
    async function stopCamera() {
        const activeScanner = scanner;
        scanner = null;

        if (activeScanner) {
            try {
                if (activeScanner.isScanning) {
                    await activeScanner.stop();
                }
            } catch (error) {
                // Camera may already have stopped.
            }

            try {
                await activeScanner.clear();
            } catch (error) {
                // Ignore cleanup errors.
            }
        }

        cameraPanel.hidden = true;
        cameraStart.hidden = selectedBooks.length >= MAX_BOOKS;
        cameraContainer.replaceChildren();
    }

    /*
     * START CAMERA SCANNER
     */
    cameraStart.addEventListener("click", async function () {
        if (selectedBooks.length >= MAX_BOOKS) {
            setStatus("You have already selected two books.", "warning");
            return;
        }

        if (typeof Html5Qrcode === "undefined") {
            setStatus(
                "Camera library did not load. Check your internet connection.",
                "error"
            );
            return;
        }

        if (scanner) {
            return;
        }

        cameraPanel.hidden = false;
        cameraStart.hidden = true;
        cameraContainer.replaceChildren();

        try {
            const newScanner = new Html5Qrcode("issue_isbn_camera");
            scanner = newScanner;

            await newScanner.start(
                { facingMode: "environment" },
                {
                    fps: 10,
                    qrbox: { width: 230, height: 75 },
                    aspectRatio: 2.4,
                    formatsToSupport: [
                        Html5QrcodeSupportedFormats.EAN_13,
                        Html5QrcodeSupportedFormats.EAN_8,
                        Html5QrcodeSupportedFormats.UPC_A,
                        Html5QrcodeSupportedFormats.UPC_E,
                        Html5QrcodeSupportedFormats.CODE_128,
                        Html5QrcodeSupportedFormats.CODE_39,
                        Html5QrcodeSupportedFormats.CODE_93,
                        Html5QrcodeSupportedFormats.ITF
                    ]
                },

                async function (decodedText) {
                    const now = Date.now();

                    if (
                        lookupInProgress ||
                        selectedBooks.length >= MAX_BOOKS ||
                        (
                            decodedText === lastCameraValue &&
                            now - lastCameraTime < 2500
                        )
                    ) {
                        return;
                    }

                    lastCameraValue = decodedText;
                    lastCameraTime = now;

                    beep();

                    await stopCamera();
                    await lookupScannedISBN(decodedText);
                },

                function () {
                    // Ignore frames without a detected barcode.
                }
            );

            setStatus(
                "Camera active. Align the barcode inside the frame.",
                "info"
            );

        } catch (error) {
            console.error("Camera startup failed:", error);

            await stopCamera();

            setStatus(
                "Could not start the camera. Allow camera permission or use a USB scanner.",
                "error"
            );
        }
    });

    cameraStop.addEventListener("click", async function () {
        await stopCamera();
        setStatus("Camera stopped.", "info");
    });

    /*
     * FINAL CLIENT-SIDE VALIDATION
     * Server-side validation is also required.
     */
    form.addEventListener("submit", async function (event) {
        if (submitting) {
            event.preventDefault();
            return;
        }

        if (lookupInProgress) {
            event.preventDefault();

            setStatus(
                "Please wait for the barcode lookup to finish.",
                "error"
            );
            return;
        }

        if (
            selectedBooks.length < 1 ||
            selectedBooks.length > MAX_BOOKS
        ) {
            event.preventDefault();

            setStatus("Select one or two books before submitting.", "error");
            bookSearch.focus();
            return;
        }

        if (
            new Set(
                selectedBooks.map(function (book) {
                    return String(book.id);
                })
            ).size !== selectedBooks.length
        ) {
            event.preventDefault();
            setStatus("Duplicate books are not allowed.", "error");
            return;
        }

        if (!employeeSelect.value) {
            event.preventDefault();
            setStatus("Please select an employee.", "error");

            if (employeeTomSelect) {
                employeeTomSelect.focus();
            } else {
                employeeSelect.focus();
            }

            return;
        }

        if (!dueDateInput.value) {
            event.preventDefault();
            setStatus("Please select a due date.", "error");
            dueDateInput.focus();
            return;
        }

        if (dueDateInput.value < today) {
            event.preventDefault();
            setStatus("Due date cannot be before today.", "error");
            dueDateInput.focus();
            return;
        }

        // Verify selected IDs are included in the submitted form.
        const submittedIds = Array.from(
            form.querySelectorAll('input[name="book_ids"]')
        ).map(function (input) {
            return input.value;
        });

        const expectedIds = selectedBooks.map(function (book) {
            return String(book.id);
        });

        if (
            submittedIds.length !== expectedIds.length ||
            submittedIds.some(function (id, index) {
                return id !== expectedIds[index];
            })
        ) {
            event.preventDefault();

            setStatus(
                "The selected books could not be prepared for submission. Please try again.",
                "error"
            );
            return;
        }

        submitting = true;
        submitButton.disabled = true;

        submitButton.innerHTML =
            '<i class="bi bi-hourglass-split"></i> Issuing books...';

        // Allow normal form submission.
    });

    // Stop the camera when the user navigates away.
    window.addEventListener("pagehide", function () {
        if (scanner && scanner.isScanning) {
            scanner.stop().catch(function () {});
        }
    });

    // Initial page state.
    updateSelectionSummary();

    if (availableBooks.length === 0) {
        setStatus(
            "No available books were loaded. Check that the Flask view passes the books list.",
            "warning"
        );
    }
});
