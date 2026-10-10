"""Add library to employees

Revision ID: bf5d311f46b3
Revises: 116b111338e3
Create Date: 2026-10-10 11:24:32.531091

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "bf5d311f46b3"
down_revision = "116b111338e3"
branch_labels = None
depends_on = None


def upgrade():
    # ---------------------------------------------------------
    # 1. Add library_id as nullable temporarily
    # ---------------------------------------------------------
    op.add_column(
        "employees",
        sa.Column(
            "library_id",
            sa.Integer(),
            nullable=True
        )
    )

    # ---------------------------------------------------------
    # 2. Get the existing Default Library
    # ---------------------------------------------------------
    connection = op.get_bind()

    default_library_id = connection.execute(
        sa.text(
            """
            SELECT id
            FROM libraries
            WHERE name = 'Default Library'
            ORDER BY id
            LIMIT 1
            """
        )
    ).scalar()

    if default_library_id is None:
        raise RuntimeError(
            "Default Library was not found. "
            "The library migration must be applied first."
        )

    # ---------------------------------------------------------
    # 3. Assign existing employees to Default Library
    # ---------------------------------------------------------
    connection.execute(
        sa.text(
            """
            UPDATE employees
            SET library_id = :library_id
            WHERE library_id IS NULL
            """
        ),
        {
            "library_id": default_library_id
        }
    )

    # ---------------------------------------------------------
    # 4. Make library_id NOT NULL
    # ---------------------------------------------------------
    op.alter_column(
        "employees",
        "library_id",
        existing_type=sa.Integer(),
        nullable=False
    )

    # ---------------------------------------------------------
    # 5. Add foreign key constraint
    # ---------------------------------------------------------
    op.create_foreign_key(
        "fk_employees_library_id",
        "employees",
        "libraries",
        ["library_id"],
        ["id"]
    )


def downgrade():
    # ---------------------------------------------------------
    # 1. Remove foreign key
    # ---------------------------------------------------------
    op.drop_constraint(
        "fk_employees_library_id",
        "employees",
        type_="foreignkey"
    )

    # ---------------------------------------------------------
    # 2. Remove library_id
    # ---------------------------------------------------------
    op.drop_column(
        "employees",
        "library_id"
    )