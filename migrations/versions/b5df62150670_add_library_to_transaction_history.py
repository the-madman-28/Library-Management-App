"""Add library to transaction history

Revision ID: b5df62150670
Revises: bf5d311f46b3
Create Date: 2026-10-10 11:38:35.618258

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b5df62150670"
down_revision = "bf5d311f46b3"
branch_labels = None
depends_on = None


def upgrade():
    # ---------------------------------------------------------
    # 1. Add library_id as nullable temporarily
    # ---------------------------------------------------------
    op.add_column(
        "transaction_history",
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
    # 3. Assign existing transaction history to Default Library
    # ---------------------------------------------------------
    connection.execute(
        sa.text(
            """
            UPDATE transaction_history
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
        "transaction_history",
        "library_id",
        existing_type=sa.Integer(),
        nullable=False
    )

    # ---------------------------------------------------------
    # 5. Add foreign key constraint
    # ---------------------------------------------------------
    op.create_foreign_key(
        "fk_transaction_history_library_id",
        "transaction_history",
        "libraries",
        ["library_id"],
        ["id"]
    )


def downgrade():
    # ---------------------------------------------------------
    # 1. Remove foreign key
    # ---------------------------------------------------------
    op.drop_constraint(
        "fk_transaction_history_library_id",
        "transaction_history",
        type_="foreignkey"
    )

    # ---------------------------------------------------------
    # 2. Remove library_id
    # ---------------------------------------------------------
    op.drop_column(
        "transaction_history",
        "library_id"
    )