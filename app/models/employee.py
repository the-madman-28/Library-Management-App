from datetime import datetime, timezone

from app.extensions import db


class Employee(db.Model):
    __tablename__ = "employees"

    __table_args__ = (
        db.UniqueConstraint(
            "library_id",
            "employee_code",
            name="uq_employees_library_employee_code"
        ),
    )

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

    employee_code = db.Column(
        db.String(50),
        nullable=False
    )

    name = db.Column(
        db.String(150),
        nullable=False
    )

    department = db.Column(
        db.String(100),
        nullable=True
    )

    designation = db.Column(
        db.String(100),
        nullable=True
    )

    email = db.Column(
        db.String(120),
        nullable=True
    )

    phone = db.Column(
        db.String(30),
        nullable=True
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="ACTIVE"
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
        back_populates="employees"
    )

    # -----------------------------------------------------
    # ACTIVE BOOK TRANSACTIONS
    # -----------------------------------------------------

    transactions = db.relationship(
        "BookTransaction",
        back_populates="employee",
        lazy=True
    )

    def __repr__(self):
        return f"<Employee {self.employee_code} - {self.name}>"