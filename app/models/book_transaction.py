from datetime import datetime, timezone

from app.extensions import db


class BookTransaction(db.Model):
    __tablename__ = "book_transactions"

    id = db.Column(
        db.Integer,
        primary_key=True
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
        nullable=False
    )

    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("employees.id"),
        nullable=False
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

    history = db.relationship(
        "TransactionHistory",
        backref=db.backref(
            "active_transaction",
            uselist=False
        )
    )

    book = db.relationship(
        "Book",
        backref=db.backref(
            "transactions",
            lazy=True
        )
    )

    employee = db.relationship(
        "Employee",
        backref=db.backref(
            "transactions",
            lazy=True
        )
    )

    def __repr__(self):
        return (
            f"<BookTransaction "
            f"{self.id} - "
            f"{self.book_id} - "
            f"{self.employee_id}>"
        )