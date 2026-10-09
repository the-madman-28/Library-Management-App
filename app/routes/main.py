from datetime import date

from flask import Blueprint, render_template

from app.extensions import db
from app.models import (
    Book,
    Employee,
    BookTransaction,
    TransactionHistory
)


main_bp = Blueprint(
    "main",
    __name__
)


@main_bp.route("/")
def index():

    today_date = date.today()

    # =========================================
    # DASHBOARD STATISTICS
    # =========================================

    # Total number of books in the library
    total_books = Book.query.count()

    # Total number of available copies
    available_books = (
        db.session.query(
            db.func.sum(Book.available_copies)
        ).scalar()
        or 0
    )

    # Total employees
    total_employees = Employee.query.count()

    # Currently issued books
    issued_books = BookTransaction.query.count()

    # Currently overdue books
    overdue_books = BookTransaction.query.filter(
        BookTransaction.due_date < today_date
    ).count()

    # Permanent all-time transaction history
    all_time_transactions = TransactionHistory.query.count()


    # =========================================
    # RENDER DASHBOARD
    # =========================================

    return render_template(
        "dashboard.html",

        total_books=total_books,
        available_books=available_books,
        total_employees=total_employees,

        issued_books=issued_books,
        overdue_books=overdue_books,

        all_time_transactions=all_time_transactions,

        today=today_date.strftime("%d %b %Y")
    )