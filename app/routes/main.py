from datetime import date

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

from app.extensions import db
from app.models import (
    Book,
    Employee,
    BookTransaction,
    TransactionHistory,
)


main_bp = Blueprint(
    "main",
    __name__
)


# =========================================================
# PUBLIC LANDING PAGE
# =========================================================

@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    return render_template("index.html")


# =========================================================
# AUTHENTICATED DASHBOARD
# =========================================================

@main_bp.route("/dashboard")
@login_required
def dashboard():

    today_date = date.today()

    # =========================================
    # CURRENT USER'S LIBRARY
    # =========================================

    library_id = current_user.library_id

    # =========================================
    # DASHBOARD STATISTICS
    # =========================================

    total_books = Book.query.filter_by(
        library_id=library_id
    ).count()

    available_books = (
        db.session.query(
            db.func.sum(Book.available_copies)
        )
        .filter(
            Book.library_id == library_id
        )
        .scalar()
        or 0
    )

    total_employees = Employee.query.filter_by(
        library_id=library_id
    ).count()

    issued_books = BookTransaction.query.filter_by(
        library_id=library_id
    ).count()

    overdue_books = BookTransaction.query.filter(
        BookTransaction.library_id == library_id,
        BookTransaction.due_date < today_date
    ).count()

    all_time_transactions = TransactionHistory.query.filter_by(
        library_id=library_id
    ).count()

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