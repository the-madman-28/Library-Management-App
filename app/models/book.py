from datetime import datetime, timezone

from app.extensions import db



class Book(db.Model):
    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True)

    book_code = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    author = db.Column(
        db.String(150),
        nullable=True
    )

    publisher = db.Column(
        db.String(150),
        nullable=True
    )

    category = db.Column(
        db.String(100),
        nullable=True
    )

    isbn = db.Column(
        db.String(20),
        nullable=True
    )

    total_copies = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )

    available_copies = db.Column(
        db.Integer,
        nullable=False,
        default=1
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

    def __repr__(self):
        return f"<Book {self.book_code} - {self.title}>"
