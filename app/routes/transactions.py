from datetime import date

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
)
from flask_login import login_required, current_user
from sqlalchemy import or_

from app.extensions import db
from app.models import (
    Book,
    Employee,
    BookTransaction,
    TransactionHistory,
)
from app.services.isbn import (
    normalize_isbn,
    equivalent_isbns,
    ISBNValidationError,
)


transactions_bp = Blueprint(
    "transactions",
    __name__,
    url_prefix="/transactions",
)


# =========================================================
# ISSUE BOOK
# Supports one or two distinct books in one submission.
# Keeps backward compatibility with the old single book_id.
# =========================================================

@transactions_bp.route("/issue", methods=["GET", "POST"])
@login_required
def issue_book():

    library_id = current_user.library_id

    if request.method == "POST":

        # -------------------------------------------------
        # GET FORM DATA
        # New form submits multiple book_ids.
        # Old form may still submit a single book_id.
        # -------------------------------------------------

        submitted_book_ids = request.form.getlist("book_ids")

        if not submitted_book_ids:
            legacy_book_id = request.form.get("book_id")
            if legacy_book_id:
                submitted_book_ids = [legacy_book_id]

        employee_id = request.form.get("employee_id")
        due_date = request.form.get("due_date")
        remarks = request.form.get("remarks", "").strip()

        # -------------------------------------------------
        # BASIC VALIDATION
        # -------------------------------------------------

        if not submitted_book_ids or not employee_id:
            flash(
                "Please select an employee and at least one book.",
                "danger",
            )
            return redirect(url_for("transactions.issue_book"))

        if not due_date:
            flash(
                "Please select a due date.",
                "danger",
            )
            return redirect(url_for("transactions.issue_book"))

        # -------------------------------------------------
        # VALIDATE BOOK IDS
        # -------------------------------------------------

        try:
            book_id_values = [
                int(value)
                for value in submitted_book_ids
            ]
            employee_id_value = int(employee_id)

        except (TypeError, ValueError):
            flash(
                "Invalid book or employee selection.",
                "danger",
            )
            return redirect(url_for("transactions.issue_book"))

        # Require positive IDs.
        if any(book_id <= 0 for book_id in book_id_values):
            flash(
                "Invalid book selection.",
                "danger",
            )
            return redirect(url_for("transactions.issue_book"))

        if employee_id_value <= 0:
            flash(
                "Invalid employee selection.",
                "danger",
            )
            return redirect(url_for("transactions.issue_book"))

        # -------------------------------------------------
        # MAXIMUM TWO DISTINCT BOOKS
        # -------------------------------------------------

        if len(book_id_values) != len(set(book_id_values)):
            flash(
                "The same book cannot be selected more than once.",
                "danger",
            )
            return redirect(url_for("transactions.issue_book"))

        if len(book_id_values) > 2:
            flash(
                "You can issue a maximum of 2 books in one submission.",
                "danger",
            )
            return redirect(url_for("transactions.issue_book"))

        # -------------------------------------------------
        # VALIDATE DUE DATE
        # Issue date remains the server's current date,
        # as in the existing implementation.
        # -------------------------------------------------

        issue_date_obj = date.today()

        try:
            due_date_obj = date.fromisoformat(due_date)

        except (TypeError, ValueError):
            flash(
                "Please enter a valid due date.",
                "danger",
            )
            return redirect(url_for("transactions.issue_book"))

        if due_date_obj < issue_date_obj:
            flash(
                "Due date cannot be before today's date.",
                "danger",
            )
            return redirect(url_for("transactions.issue_book"))

        # -------------------------------------------------
        # GET EMPLOYEE
        # Employee must belong to the current user's library.
        # -------------------------------------------------

        employee = Employee.query.filter_by(
            id=employee_id_value,
            library_id=library_id,
        ).first()

        if not employee:
            flash(
                "Selected employee does not exist.",
                "danger",
            )
            return redirect(url_for("transactions.issue_book"))

        if employee.status != "ACTIVE":
            flash(
                "This employee is inactive and cannot borrow books.",
                "danger",
            )
            return redirect(url_for("transactions.issue_book"))

        # -------------------------------------------------
        # GET ALL BOOKS
        # All selected books must belong to this library.
        # Lock matching rows where supported by the database.
        # -------------------------------------------------

        books = (
            Book.query
            .filter(
                Book.id.in_(book_id_values),
                Book.library_id == library_id,
            )
            .with_for_update()
            .all()
        )

        books_by_id = {
            book.id: book
            for book in books
        }

        # Do not proceed if any ID was missing or belongs
        # to another library.
        if len(books_by_id) != len(book_id_values):
            flash(
                "One or more selected books do not exist in your library.",
                "danger",
            )
            return redirect(url_for("transactions.issue_book"))

        # Preserve the order in which the user selected books.
        selected_books = [
            books_by_id[book_id]
            for book_id in book_id_values
        ]

        # -------------------------------------------------
        # CHECK AVAILABILITY BEFORE MAKING ANY CHANGES
        # -------------------------------------------------

        unavailable_books = [
            book.title
            for book in selected_books
            if book.available_copies <= 0
        ]

        if unavailable_books:
            flash(
                "Not enough copies available for: "
                + ", ".join(unavailable_books),
                "danger",
            )
            return redirect(url_for("transactions.issue_book"))

        # =================================================
        # CREATE ALL RECORDS AND UPDATE INVENTORY
        # All selected books are handled in one transaction.
        # =================================================

        try:
            for book in selected_books:

                # -----------------------------------------
                # PERMANENT HISTORY RECORD
                # -----------------------------------------

                history = TransactionHistory(
                    library_id=library_id,
                    book_code=book.book_code,
                    book_title=book.title,
                    employee_code=employee.employee_code,
                    employee_name=employee.name,
                    issue_date=issue_date_obj,
                    due_date=due_date_obj,
                    return_date=None,
                    status="ISSUED",
                    remarks=remarks or None,
                )

                db.session.add(history)

                # Generate the history ID before creating
                # the active transaction.
                db.session.flush()

                # -----------------------------------------
                # ACTIVE TRANSACTION
                # -----------------------------------------

                transaction = BookTransaction(
                    library_id=library_id,
                    history_id=history.id,
                    book_id=book.id,
                    employee_id=employee.id,
                    issue_date=issue_date_obj,
                    due_date=due_date_obj,
                    remarks=remarks or None,
                )

                db.session.add(transaction)

                # -----------------------------------------
                # UPDATE INVENTORY
                # -----------------------------------------

                book.available_copies -= 1

            # Commit all selected books together.
            db.session.commit()

        except Exception:
            db.session.rollback()

            flash(
                "Unable to issue the selected books. "
                "No changes were saved. Please try again.",
                "danger",
            )
            return redirect(url_for("transactions.issue_book"))

        # -------------------------------------------------
        # SUCCESS MESSAGE
        # -------------------------------------------------

        if len(selected_books) == 1:
            flash(
                f"Book '{selected_books[0].title}' issued to "
                f"{employee.name} successfully.",
                "success",
            )
        else:
            titles = ", ".join(
                f"'{book.title}'"
                for book in selected_books
            )
            flash(
                f"{len(selected_books)} books ({titles}) issued to "
                f"{employee.name} successfully.",
                "success",
            )

        return redirect(url_for("transactions.issue_book"))

    # =====================================================
    # GET
    # =====================================================

    books = Book.query.filter(
        Book.library_id == library_id,
        Book.available_copies > 0,
    ).order_by(
        Book.title.asc()
    ).all()

    employees = Employee.query.filter(
        Employee.library_id == library_id,
        Employee.status == "ACTIVE",
    ).order_by(
        Employee.name.asc()
    ).all()

    return render_template(
        "transactions/issue.html",
        books=books,
        employees=employees,
        today=date.today().isoformat(),
    )


# =========================================================
# ISBN LOOKUP FOR ISSUE BOOK
# =========================================================

@transactions_bp.route("/lookup-issue-isbn", methods=["POST"])
@login_required
def lookup_issue_isbn():

    library_id = current_user.library_id
    data = request.get_json(silent=True) or {}
    scanned_isbn = data.get("isbn", "")

    # -----------------------------------------------------
    # VALIDATE AND NORMALIZE ISBN
    # -----------------------------------------------------

    try:
        normalized_isbn = normalize_isbn(scanned_isbn)
        matching_isbns = list(equivalent_isbns(normalized_isbn))

    except (ISBNValidationError, TypeError, ValueError):
        return jsonify({
            "ok": False,
            "message": "Invalid ISBN barcode. Please scan a valid ISBN.",
        }), 400

    # -----------------------------------------------------
    # FIND BOOK IN THE CURRENT LIBRARY
    # -----------------------------------------------------

    books = Book.query.filter(
        Book.library_id == library_id,
        Book.isbn.in_(matching_isbns),
    ).order_by(
        Book.id.asc()
    ).all()

    if not books:
        return jsonify({
            "ok": False,
            "message": "This ISBN was not found in your library.",
        }), 404

    # Do not guess if multiple database records match.
    if len(books) > 1:
        return jsonify({
            "ok": False,
            "message": (
                "Multiple books match this ISBN. "
                "Please select the correct book manually."
            ),
        }), 409

    book = books[0]

    if book.available_copies <= 0:
        return jsonify({
            "ok": False,
            "message": f"'{book.title}' has no available copies.",
            "book": {
                "id": book.id,
                "book_code": book.book_code,
                "title": book.title,
                "isbn": book.isbn,
                "available_copies": book.available_copies,
            },
        }), 409

    return jsonify({
        "ok": True,
        "message": "Book found and available.",
        "book": {
            "id": book.id,
            "book_code": book.book_code,
            "title": book.title,
            "isbn": book.isbn,
            "available_copies": book.available_copies,
        },
    })


# =========================================================
# RETURN BOOK
# =========================================================

@transactions_bp.route("/return", methods=["GET", "POST"])
@login_required
def return_book():
    """Return one or more active loans belonging to the current library."""
    library_id = current_user.library_id

    if request.method == "POST":
        # Support the new multi-select form and the previous single-ID form.
        submitted_ids = request.form.getlist("transaction_ids")
        legacy_id = request.form.get("transaction_id")
        if not submitted_ids and legacy_id:
            submitted_ids = [legacy_id]

        if not submitted_ids:
            flash("Please select at least one issued book.", "danger")
            return redirect(url_for("transactions.return_book"))

        try:
            transaction_ids = [int(value) for value in submitted_ids]
        except (TypeError, ValueError):
            flash("Invalid transaction selection.", "danger")
            return redirect(url_for("transactions.return_book"))

        if any(value <= 0 for value in transaction_ids) or len(transaction_ids) != len(set(transaction_ids)):
            flash("Invalid or duplicate transaction selection.", "danger")
            return redirect(url_for("transactions.return_book"))

        try:
            # Lock selected active loans where supported. No changes are committed
            # unless every selected loan passes validation.
            selected_transactions = (
                BookTransaction.query
                .filter(
                    BookTransaction.id.in_(transaction_ids),
                    BookTransaction.library_id == library_id,
                )
                .with_for_update()
                .all()
            )

            transaction_by_id = {item.id: item for item in selected_transactions}
            if len(transaction_by_id) != len(transaction_ids):
                db.session.rollback()
                flash("One or more selected loans were not found or are no longer active.", "danger")
                return redirect(url_for("transactions.return_book"))

            # Preserve selection order and validate all related records first.
            ordered_transactions = [transaction_by_id[item_id] for item_id in transaction_ids]
            for transaction in ordered_transactions:
                book = transaction.book
                history = transaction.history
                if not book or not history:
                    raise ValueError("A selected loan is missing its book or history record.")
                if book.library_id != library_id or history.library_id != library_id:
                    raise PermissionError("A selected loan does not belong to your library.")

            today = date.today()
            returned_titles = []
            for transaction in ordered_transactions:
                book = transaction.book
                history = transaction.history

                history.return_date = today
                history.status = "RETURNED"

                # Restore exactly one copy for this active loan.
                book.available_copies = min(book.available_copies + 1, book.total_copies)
                returned_titles.append(book.title)
                db.session.delete(transaction)

            db.session.commit()

        except PermissionError:
            db.session.rollback()
            flash("You are not authorized to return one or more selected loans.", "danger")
            return redirect(url_for("transactions.return_book"))
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), "danger")
            return redirect(url_for("transactions.return_book"))
        except Exception:
            db.session.rollback()
            flash("Unable to process the book return. No changes were saved. Please try again.", "danger")
            return redirect(url_for("transactions.return_book"))

        if len(returned_titles) == 1:
            flash(f"Book '{returned_titles[0]}' returned successfully.", "success")
        else:
            flash(f"{len(returned_titles)} books returned successfully.", "success")
        return redirect(url_for("transactions.return_book"))

    # Do not preload every issued loan into the page. Search results are fetched
    # only when the user types a query or scans an ISBN.
    return render_template("transactions/return.html")


# =========================================================
# ISBN LOOKUP FOR RETURN BOOK
# =========================================================

@transactions_bp.route("/search-return-loans", methods=["GET"])
@login_required
def search_return_loans():
    """Search active loans on demand; never expose loans from other libraries."""
    library_id = current_user.library_id
    term = request.args.get("q", "").strip()

    if len(term) < 2:
        return jsonify({"ok": True, "matches": []})

    pattern = f"%{term}%"
    query = (
        BookTransaction.query
        .join(Book, BookTransaction.book_id == Book.id)
        .join(Employee, BookTransaction.employee_id == Employee.id)
        .filter(
            BookTransaction.library_id == library_id,
            Book.library_id == library_id,
            Employee.library_id == library_id,
            or_(
                Book.title.ilike(pattern),
                Book.book_code.ilike(pattern),
                Book.isbn.ilike(pattern),
                Employee.name.ilike(pattern),
                Employee.employee_code.ilike(pattern),
            ),
        )
        .order_by(Employee.name.asc(), BookTransaction.due_date.asc())
        .limit(50)
        .all()
    )

    matches = []
    for transaction in query:
        book = transaction.book
        employee = transaction.employee
        if not book or not employee:
            continue
        matches.append({
            "transaction_id": transaction.id,
            "book_id": book.id,
            "book_code": book.book_code,
            "book_title": book.title,
            "isbn": book.isbn or "",
            "employee_id": employee.id,
            "employee_code": employee.employee_code,
            "employee_name": employee.name,
            "issue_date": transaction.issue_date.isoformat() if transaction.issue_date else "",
            "due_date": transaction.due_date.isoformat() if transaction.due_date else "",
        })

    return jsonify({"ok": True, "matches": matches, "count": len(matches)})


@transactions_bp.route("/lookup-return-isbn", methods=["POST"])
@login_required
def lookup_return_isbn():

    library_id = current_user.library_id
    data = request.get_json(silent=True) or {}
    scanned_isbn = data.get("isbn", "")

    # -----------------------------------------------------
    # VALIDATE AND NORMALIZE ISBN
    # -----------------------------------------------------

    try:
        normalized_isbn = normalize_isbn(scanned_isbn)
        matching_isbns = list(equivalent_isbns(normalized_isbn))

    except (ISBNValidationError, TypeError, ValueError):
        return jsonify({
            "ok": False,
            "message": "Invalid ISBN barcode. Please scan a valid ISBN.",
            "matches": [],
        }), 400

    # -----------------------------------------------------
    # FIND ACTIVE LOANS FOR THIS ISBN
    # -----------------------------------------------------

    active_transactions = (
        BookTransaction.query
        .join(Book, BookTransaction.book_id == Book.id)
        .filter(
            BookTransaction.library_id == library_id,
            Book.library_id == library_id,
            Book.isbn.in_(matching_isbns),
        )
        .order_by(
            BookTransaction.due_date.asc()
        )
        .all()
    )

    if not active_transactions:
        return jsonify({
            "ok": False,
            "message": (
                "No active loan was found for this ISBN. "
                "The book may not be issued, or its ISBN may not match."
            ),
            "matches": [],
        }), 404

    # -----------------------------------------------------
    # BUILD MATCHING LOAN DETAILS
    # -----------------------------------------------------

    matches = []

    for transaction in active_transactions:

        book = transaction.book
        employee = transaction.employee

        if not book or not employee:
            continue

        matches.append({
            "transaction_id": transaction.id,
            "book_id": book.id,
            "employee_id": employee.id,
            "book_code": book.book_code,
            "book_title": book.title,
            "isbn": book.isbn,
            "employee_code": employee.employee_code,
            "employee_name": employee.name,
            "issue_date": transaction.issue_date.isoformat(),
            "due_date": transaction.due_date.isoformat(),
            "return_date": date.today().isoformat(),
            "label": (
                f"{book.book_code} - {book.title} | "
                f"{employee.employee_code} - {employee.name} | "
                f"Due: {transaction.due_date}"
            ),
        })

    if not matches:
        return jsonify({
            "ok": False,
            "message": "No valid active loan was found for this ISBN.",
            "matches": [],
        }), 404

    return jsonify({
        "ok": True,
        "message": (
            "One active loan found."
            if len(matches) == 1
            else (
                f"{len(matches)} active loans found. "
                "Select the correct borrower."
            )
        ),
        "matches": matches,
    })


# =========================================================
# CURRENTLY ISSUED BOOKS
# =========================================================

@transactions_bp.route("/issued")
@login_required
def issued_books():

    library_id = current_user.library_id

    search_query = request.args.get("q", "").strip()

    query = BookTransaction.query.filter(
        BookTransaction.library_id == library_id
    )

    # -----------------------------------------------------
    # DATABASE-SIDE SEARCH
    # -----------------------------------------------------

    if search_query:
        search = f"%{search_query}%"

        query = query.join(
            Book
        ).join(
            Employee
        ).filter(
            or_(
                Book.book_code.ilike(search),
                Book.title.ilike(search),
                Employee.employee_code.ilike(search),
                Employee.name.ilike(search),
            )
        )

    # -----------------------------------------------------
    # PAGINATION
    # -----------------------------------------------------

    page = request.args.get("page", 1, type=int)
    per_page = 10

    pagination = query.order_by(
        BookTransaction.due_date.asc()
    ).paginate(
        page=page,
        per_page=per_page,
        error_out=False,
    )

    return render_template(
        "transactions/issued.html",
        transactions=pagination.items,
        pagination=pagination,
        today=date.today(),
        search_query=search_query,
    )


# =========================================================
# OVERDUE BOOKS
# =========================================================

@transactions_bp.route("/overdue")
@login_required
def overdue_books():

    library_id = current_user.library_id

    search_query = request.args.get("q", "").strip()

    query = BookTransaction.query.filter(
        BookTransaction.library_id == library_id,
        BookTransaction.due_date < date.today(),
    )

    # -----------------------------------------------------
    # DATABASE-SIDE SEARCH
    # -----------------------------------------------------

    if search_query:
        search = f"%{search_query}%"

        query = query.join(
            Book
        ).join(
            Employee
        ).filter(
            or_(
                Book.book_code.ilike(search),
                Book.title.ilike(search),
                Employee.employee_code.ilike(search),
                Employee.name.ilike(search),
            )
        )

    # -----------------------------------------------------
    # PAGINATION
    # -----------------------------------------------------

    page = request.args.get("page", 1, type=int)
    per_page = 10

    pagination = query.order_by(
        BookTransaction.due_date.asc()
    ).paginate(
        page=page,
        per_page=per_page,
        error_out=False,
    )

    return render_template(
        "transactions/overdue.html",
        transactions=pagination.items,
        pagination=pagination,
        today=date.today(),
        search_query=search_query,
    )


# =========================================================
# ALL-TIME TRANSACTION HISTORY
# =========================================================

@transactions_bp.route("/history")
@login_required
def transaction_history():

    library_id = current_user.library_id

    search_query = request.args.get("q", "").strip()

    query = TransactionHistory.query.filter(
        TransactionHistory.library_id == library_id
    )

    # -----------------------------------------------------
    # DATABASE-SIDE SEARCH
    # -----------------------------------------------------

    if search_query:

        search = f"%{search_query}%"

        query = query.filter(
            or_(
                TransactionHistory.book_code.ilike(search),
                TransactionHistory.book_title.ilike(search),
                TransactionHistory.employee_code.ilike(search),
                TransactionHistory.employee_name.ilike(search),
                TransactionHistory.status.ilike(search),
                TransactionHistory.remarks.ilike(search),
            )
        )

    # -----------------------------------------------------
    # PAGINATION
    # -----------------------------------------------------

    page = request.args.get("page", 1, type=int)
    per_page = 10

    pagination = query.order_by(
        TransactionHistory.created_at.desc()
    ).paginate(
        page=page,
        per_page=per_page,
        error_out=False,
    )

    return render_template(
        "transactions/history.html",
        history=pagination.items,
        pagination=pagination,
        search_query=search_query,
    )
