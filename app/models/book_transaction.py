from datetime import datetime, timezone

from app.extensions import db


class BookTransaction(db.Model):
    __tablename__ = "book_transactions"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    library_id = db.Column(
        db.Integer,
        db.ForeignKey("libraries.id"),
        nullable=False,
        index=True
    )

    history_id = db.Column(
        db.Integer,
        db.ForeignKey("transaction_history.id"),
        nullable=False,
        unique=True
    )

    book_id = db.Column(
        db.Integer,
        db.ForeignKey("books.id"),
        nullable=False,
        index=True
    )

    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("employees.id"),
        nullable=False,
        index=True
    )

    issue_date = db.Column(
        db.Date,
        nullable=False
    )

    due_date = db.Column(
        db.Date,
        nullable=False
    )

    remarks = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    # -----------------------------------------------------
    # TRANSACTION HISTORY RELATIONSHIP
    # -----------------------------------------------------

    history = db.relationship(
        "TransactionHistory",
        back_populates="active_transaction"
    )

    # -----------------------------------------------------
    # BOOK RELATIONSHIP
    # -----------------------------------------------------

    book = db.relationship(
        "Book",
        back_populates="transactions"
    )

    # -----------------------------------------------------
    # EMPLOYEE RELATIONSHIP
    # -----------------------------------------------------

    employee = db.relationship(
        "Employee",
        back_populates="transactions"
    )

    # -----------------------------------------------------
    # LIBRARY RELATIONSHIP
    # -----------------------------------------------------

    library = db.relationship(
        "Library",
        back_populates="book_transactions"
    )

    def __repr__(self):
        return (
            f"<BookTransaction "
            f"{self.id} - "
            f"{self.book_id} - "
            f"{self.employee_id}>"
        )