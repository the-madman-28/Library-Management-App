"""Add library to book transactions

Revision ID: f858fdbad6ad
Revises: b5df62150670
Create Date: 2026-10-10 11:41:17.935174

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f858fdbad6ad"
down_revision = "b5df62150670"
branch_labels = None
depends_on = None


def upgrade():
    # ---------------------------------------------------------
    # 1. Add library_id as nullable temporarily
    # ---------------------------------------------------------
    op.add_column(
        "book_transactions",
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
    # 3. Assign existing active transactions to Default Library
    # ---------------------------------------------------------
    connection.execute(
        sa.text(
            """
            UPDATE book_transactions
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
        "book_transactions",
        "library_id",
        existing_type=sa.Integer(),
        nullable=False
    )

    # ---------------------------------------------------------
    # 5. Add foreign key constraint
    # ---------------------------------------------------------
    op.create_foreign_key(
        "fk_book_transactions_library_id",
        "book_transactions",
        "libraries",
        ["library_id"],
        ["id"]
    )


def downgrade():
    # ---------------------------------------------------------
    # 1. Remove foreign key
    # ---------------------------------------------------------
    op.drop_constraint(
        "fk_book_transactions_library_id",
        "book_transactions",
        type_="foreignkey"
    )

    # ---------------------------------------------------------
    # 2. Remove library_id
    # ---------------------------------------------------------
    op.drop_column(
        "book_transactions",
        "library_id"
    )