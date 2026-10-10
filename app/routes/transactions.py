from datetime import date

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
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


transactions_bp = Blueprint(
    "transactions",
    __name__,
    url_prefix="/transactions",
)


# =========================================================
# ISSUE BOOK
# =========================================================

@transactions_bp.route(
    "/issue",
    methods=["GET", "POST"]
)
@login_required
def issue_book():

    library_id = current_user.library_id

    if request.method == "POST":

        book_id = request.form.get("book_id")
        employee_id = request.form.get("employee_id")

        issue_date = request.form.get("issue_date")
        due_date = request.form.get("due_date")

        remarks = request.form.get(
            "remarks",
            ""
        ).strip()

        # -------------------------------------------------
        # BASIC VALIDATION
        # -------------------------------------------------

        if not book_id or not employee_id:
            flash(
                "Please select both an employee and a book.",
                "danger"
            )
            return redirect(
                url_for("transactions.issue_book")
            )

        if not issue_date or not due_date:
            flash(
                "Issue date and due date are required.",
                "danger"
            )
            return redirect(
                url_for("transactions.issue_book")
            )

        # -------------------------------------------------
        # VALIDATE IDS
        # -------------------------------------------------

        try:
            book_id_value = int(book_id)
            employee_id_value = int(employee_id)

        except (TypeError, ValueError):
            flash(
                "Invalid book or employee selection.",
                "danger"
            )
            return redirect(
                url_for("transactions.issue_book")
            )

        # -------------------------------------------------
        # GET BOOK AND EMPLOYEE
        # IMPORTANT:
        # Both must belong to current user's library.
        # -------------------------------------------------

        book = Book.query.filter_by(
            id=book_id_value,
            library_id=library_id,
        ).first()

        employee = Employee.query.filter_by(
            id=employee_id_value,
            library_id=library_id,
        ).first()

        if not book:
            flash(
                "Selected book does not exist.",
                "danger"
            )
            return redirect(
                url_for("transactions.issue_book")
            )

        if not employee:
            flash(
                "Selected employee does not exist.",
                "danger"
            )
            return redirect(
                url_for("transactions.issue_book")
            )

        # -------------------------------------------------
        # EMPLOYEE VALIDATION
        # -------------------------------------------------

        if employee.status != "ACTIVE":
            flash(
                "This employee is inactive and cannot borrow books.",
                "danger"
            )
            return redirect(
                url_for("transactions.issue_book")
            )

        # -------------------------------------------------
        # BOOK AVAILABILITY
        # -------------------------------------------------

        if book.available_copies <= 0:
            flash(
                "This book currently has no available copies.",
                "danger"
            )
            return redirect(
                url_for("transactions.issue_book")
            )

        # -------------------------------------------------
        # DATE VALIDATION
        # -------------------------------------------------

        try:
            issue_date_obj = date.fromisoformat(
                issue_date
            )

            due_date_obj = date.fromisoformat(
                due_date
            )

        except ValueError:
            flash(
                "Please enter valid dates.",
                "danger"
            )
            return redirect(
                url_for("transactions.issue_book")
            )

        if due_date_obj < issue_date_obj:
            flash(
                "Due date cannot be before the issue date.",
                "danger"
            )
            return redirect(
                url_for("transactions.issue_book")
            )

        # =================================================
        # CREATE PERMANENT HISTORY RECORD
        # =================================================

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

        # Generate history.id before creating
        # the active transaction.
        db.session.flush()

        # =================================================
        # CREATE CURRENT ACTIVE TRANSACTION
        # =================================================

        transaction = BookTransaction(
            library_id=library_id,
            history_id=history.id,
            book_id=book.id,
            employee_id=employee.id,
            issue_date=issue_date_obj,
            due_date=due_date_obj,
            remarks=remarks or None,
        )

        # =================================================
        # UPDATE INVENTORY
        # =================================================

        book.available_copies -= 1

        db.session.add(transaction)

        # =================================================
        # COMMIT EVERYTHING TOGETHER
        # =================================================

        try:
            db.session.commit()

        except Exception:
            db.session.rollback()

            flash(
                "Unable to issue the book. Please try again.",
                "danger"
            )

            return redirect(
                url_for("transactions.issue_book")
            )

        flash(
            f"Book '{book.title}' issued to {employee.name}.",
            "success"
        )

        return redirect(
            url_for("transactions.issue_book")
        )

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
        today=date.today().isoformat()
    )


# =========================================================
# RETURN BOOK
# =========================================================

@transactions_bp.route(
    "/return",
    methods=["GET", "POST"]
)
@login_required
def return_book():

    library_id = current_user.library_id

    if request.method == "POST":

        transaction_id = request.form.get(
            "transaction_id"
        )

        # -------------------------------------------------
        # BASIC VALIDATION
        # -------------------------------------------------

        if not transaction_id:
            flash(
                "Please select an issued book.",
                "danger"
            )
            return redirect(
                url_for("transactions.return_book")
            )

        # -------------------------------------------------
        # GET ACTIVE TRANSACTION
        # IMPORTANT:
        # Must belong to current user's library.
        # -------------------------------------------------

        try:
            transaction_id_value = int(
                transaction_id
            )

        except (TypeError, ValueError):
            flash(
                "Invalid transaction selection.",
                "danger"
            )
            return redirect(
                url_for("transactions.return_book")
            )

        transaction = BookTransaction.query.filter_by(
            id=transaction_id_value,
            library_id=library_id,
        ).first()

        if not transaction:
            flash(
                "Transaction not found.",
                "danger"
            )
            return redirect(
                url_for("transactions.return_book")
            )

        # -------------------------------------------------
        # GET RELATED OBJECTS
        # -------------------------------------------------

        book = transaction.book
        history = transaction.history

        if not book:
            flash(
                "The associated book could not be found.",
                "danger"
            )
            return redirect(
                url_for("transactions.return_book")
            )

        if not history:
            flash(
                "Transaction history record could not be found.",
                "danger"
            )
            return redirect(
                url_for("transactions.return_book")
            )

        # Extra tenant-safety checks
        if book.library_id != library_id:
            flash(
                "You are not authorized to access this book.",
                "danger"
            )
            return redirect(
                url_for("transactions.return_book")
            )

        if history.library_id != library_id:
            flash(
                "You are not authorized to access this transaction history.",
                "danger"
            )
            return redirect(
                url_for("transactions.return_book")
            )

        # =================================================
        # UPDATE PERMANENT HISTORY
        # =================================================

        history.return_date = date.today()
        history.status = "RETURNED"

        # =================================================
        # RESTORE INVENTORY
        # =================================================

        book.available_copies += 1

        # Prevent inventory from accidentally exceeding
        # the book's total number of copies.
        if book.available_copies > book.total_copies:
            book.available_copies = book.total_copies

        # =================================================
        # REMOVE ACTIVE TRANSACTION
        # =================================================

        db.session.delete(transaction)

        # =================================================
        # COMMIT EVERYTHING TOGETHER
        # =================================================

        try:
            db.session.commit()

        except Exception:
            db.session.rollback()

            flash(
                "Unable to process the book return. "
                "Please try again.",
                "danger"
            )

            return redirect(
                url_for("transactions.return_book")
            )

        flash(
            f"Book '{book.title}' returned successfully.",
            "success"
        )

        return redirect(
            url_for("transactions.return_book")
        )

    # =====================================================
    # GET
    # =====================================================

    transactions = BookTransaction.query.filter_by(
        library_id=library_id
    ).order_by(
        BookTransaction.due_date.asc()
    ).all()

    return render_template(
        "transactions/return.html",
        transactions=transactions
    )


# =========================================================
# CURRENTLY ISSUED BOOKS
# =========================================================

@transactions_bp.route("/issued")
@login_required
def issued_books():

    library_id = current_user.library_id

    search_query = request.args.get(
        "q",
        ""
    ).strip()

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
                Employee.name.ilike(search)
            )
        )

    transactions = query.order_by(
        BookTransaction.due_date.asc()
    ).all()

    return render_template(
        "transactions/issued.html",
        transactions=transactions,
        today=date.today(),
        search_query=search_query
    )


# =========================================================
# OVERDUE BOOKS
# =========================================================

@transactions_bp.route("/overdue")
@login_required
def overdue_books():

    library_id = current_user.library_id

    search_query = request.args.get(
        "q",
        ""
    ).strip()

    query = BookTransaction.query.filter(
        BookTransaction.library_id == library_id,
        BookTransaction.due_date < date.today()
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
                Employee.name.ilike(search)
            )
        )

    transactions = query.order_by(
        BookTransaction.due_date.asc()
    ).all()

    return render_template(
        "transactions/overdue.html",
        transactions=transactions,
        today=date.today(),
        search_query=search_query
    )


# =========================================================
# ALL-TIME TRANSACTION HISTORY
# =========================================================

@transactions_bp.route("/history")
@login_required
def transaction_history():

    library_id = current_user.library_id

    search_query = request.args.get(
        "q",
        ""
    ).strip()

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
                TransactionHistory.remarks.ilike(search)
            )
        )

    history = query.order_by(
        TransactionHistory.created_at.desc()
    ).all()

    return render_template(
        "transactions/history.html",
        history=history,
        search_query=search_query
    )