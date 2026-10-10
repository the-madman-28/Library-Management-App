from datetime import datetime, timezone

from app.extensions import db


class TransactionHistory(db.Model):
    __tablename__ = "transaction_history"

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

    book_code = db.Column(
        db.String(50),
        nullable=False
    )

    book_title = db.Column(
        db.String(200),
        nullable=False
    )

    employee_code = db.Column(
        db.String(50),
        nullable=False
    )

    employee_name = db.Column(
        db.String(150),
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

    return_date = db.Column(
        db.Date,
        nullable=True
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="ISSUED"
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
    # LIBRARY RELATIONSHIP
    # -----------------------------------------------------

    library = db.relationship(
        "Library",
        back_populates="transaction_history"
    )

    # -----------------------------------------------------
    # ACTIVE TRANSACTION RELATIONSHIP
    # -----------------------------------------------------
    #
    # A history record can have zero or one active
    # transaction.
    #
    # When a book is returned, the BookTransaction record
    # is deleted but this history record remains permanently.
    # -----------------------------------------------------

    active_transaction = db.relationship(
        "BookTransaction",
        back_populates="history",
        uselist=False
    )

    def __repr__(self):
        return (
            f"<TransactionHistory "
            f"{self.id} - "
            f"{self.book_code} - "
            f"{self.employee_code} - "
            f"{self.status}>"
        )