from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import (
    generate_password_hash,
    check_password_hash,
)

from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

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

    username = db.Column(
        db.String(80),
        unique=True,
        nullable=False,
        index=True
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False,
        index=True
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.String(20),
        nullable=False,
        default="librarian"
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True
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
    # LIBRARY RELATIONSHIP
    # -----------------------------------------------------

    library = db.relationship(
        "Library",
        back_populates="users"
    )

    # -----------------------------------------------------
    # PASSWORD MANAGEMENT
    # -----------------------------------------------------

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(
            self.password_hash,
            password
        )

    # -----------------------------------------------------
    # REPRESENTATION
    # -----------------------------------------------------

    def __repr__(self):
        return f"<User {self.username}>"