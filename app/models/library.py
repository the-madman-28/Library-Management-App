from datetime import datetime, timezone

from app.extensions import db


class Library(db.Model):
    __tablename__ = "libraries"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(150),
        nullable=False,
        unique=True
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # -----------------------------------------------------
    # USERS BELONGING TO THIS LIBRARY
    # -----------------------------------------------------

    users = db.relationship(
        "User",
        back_populates="library",
        lazy=True
    )

    # -----------------------------------------------------
    # BOOKS BELONGING TO THIS LIBRARY
    # -----------------------------------------------------

    books = db.relationship(
        "Book",
        back_populates="library",
        lazy=True
    )

    # -----------------------------------------------------
    # EMPLOYEES BELONGING TO THIS LIBRARY
    # -----------------------------------------------------

    employees = db.relationship(
        "Employee",
        back_populates="library",
        lazy=True
    )

    # -----------------------------------------------------
    # ACTIVE BOOK TRANSACTIONS
    # -----------------------------------------------------

    book_transactions = db.relationship(
        "BookTransaction",
        back_populates="library",
        lazy=True
    )

    # -----------------------------------------------------
    # PERMANENT TRANSACTION HISTORY
    # -----------------------------------------------------

    transaction_history = db.relationship(
        "TransactionHistory",
        back_populates="library",
        lazy=True
    )

    def __repr__(self):
        return f"<Library {self.id} - {self.name}>"