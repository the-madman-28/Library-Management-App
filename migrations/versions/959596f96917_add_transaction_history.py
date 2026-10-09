"""Add transaction history

Revision ID: 959596f96917
Revises: 1df85380850d
Create Date: 2026-10-08 10:33:18.806650

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "959596f96917"
down_revision = "1df85380850d"
branch_labels = None
depends_on = None


def upgrade():
    # ---------------------------------------------------------
    # 1. Create transaction_history
    # ---------------------------------------------------------
    op.create_table(
        "transaction_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("book_code", sa.String(length=50), nullable=False),
        sa.Column("book_title", sa.String(length=200), nullable=False),
        sa.Column("employee_code", sa.String(length=50), nullable=False),
        sa.Column("employee_name", sa.String(length=150), nullable=False),
        sa.Column("issue_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("return_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # ---------------------------------------------------------
    # 2. Add history_id temporarily as nullable
    #
    # Existing book_transactions rows need a history record
    # before history_id can become NOT NULL.
    # ---------------------------------------------------------
    with op.batch_alter_table(
        "book_transactions",
        schema=None
    ) as batch_op:
        batch_op.add_column(
            sa.Column(
                "history_id",
                sa.Integer(),
                nullable=True
            )
        )

    # ---------------------------------------------------------
    # 3. Create a history record for every existing transaction
    #
    # This preserves existing transaction data if the database
    # already contains book transactions.
    # ---------------------------------------------------------
    op.execute(
        sa.text(
            """
            INSERT INTO transaction_history (
                book_code,
                book_title,
                employee_code,
                employee_name,
                issue_date,
                due_date,
                return_date,
                status,
                remarks,
                created_at
            )
            SELECT
                b.book_code,
                b.title,
                e.employee_code,
                e.name,
                bt.issue_date,
                bt.due_date,
                bt.return_date,
                bt.status,
                bt.remarks,
                CURRENT_TIMESTAMP
            FROM book_transactions bt
            JOIN books b
                ON b.id = bt.book_id
            JOIN employees e
                ON e.id = bt.employee_id
            """
        )
    )

    # ---------------------------------------------------------
    # 4. Link each existing book transaction to the history row
    #
    # SQLite does not provide a simple RETURNING-based mapping
    # suitable for this migration, so match using the original
    # transaction fields.
    # ---------------------------------------------------------
    op.execute(
        sa.text(
            """
            UPDATE book_transactions
            SET history_id = (
                SELECT th.id
                FROM transaction_history th
                JOIN books b
                    ON b.book_code = th.book_code
                JOIN employees e
                    ON e.employee_code = th.employee_code
                WHERE b.id = book_transactions.book_id
                  AND e.id = book_transactions.employee_id
                  AND th.issue_date = book_transactions.issue_date
                  AND th.due_date = book_transactions.due_date
                ORDER BY th.id DESC
                LIMIT 1
            )
            """
        )
    )

    # ---------------------------------------------------------
    # 5. Convert book_transactions to the new structure
    #
    # Named constraints are required for SQLite batch mode.
    # ---------------------------------------------------------
    with op.batch_alter_table(
        "book_transactions",
        schema=None
    ) as batch_op:
        batch_op.alter_column(
            "history_id",
            existing_type=sa.Integer(),
            nullable=False
        )

        batch_op.create_unique_constraint(
            "uq_book_transactions_history_id",
            ["history_id"]
        )

        batch_op.create_foreign_key(
            "fk_book_transactions_history_id",
            "transaction_history",
            ["history_id"],
            ["id"]
        )

        batch_op.drop_column("return_date")
        batch_op.drop_column("status")


def downgrade():
    # ---------------------------------------------------------
    # 1. Restore old columns
    # ---------------------------------------------------------
    with op.batch_alter_table(
        "book_transactions",
        schema=None
    ) as batch_op:
        batch_op.add_column(
            sa.Column(
                "status",
                sa.String(length=20),
                nullable=True
            )
        )

        batch_op.add_column(
            sa.Column(
                "return_date",
                sa.Date(),
                nullable=True
            )
        )

        # Restore status/return_date from transaction history.
        #
        # The actual values are populated in the second batch
        # operation below after the columns exist.
        batch_op.drop_constraint(
            "fk_book_transactions_history_id",
            type_="foreignkey"
        )

        batch_op.drop_constraint(
            "uq_book_transactions_history_id",
            type_="unique"
        )

        batch_op.drop_column("history_id")

    # ---------------------------------------------------------
    # 2. Restore values from transaction_history
    # ---------------------------------------------------------
    op.execute(
        sa.text(
            """
            UPDATE book_transactions
            SET
                status = (
                    SELECT th.status
                    FROM transaction_history th
                    WHERE th.book_code = (
                        SELECT b.book_code
                        FROM books b
                        WHERE b.id = book_transactions.book_id
                    )
                    AND th.employee_code = (
                        SELECT e.employee_code
                        FROM employees e
                        WHERE e.id = book_transactions.employee_id
                    )
                    AND th.issue_date = book_transactions.issue_date
                    AND th.due_date = book_transactions.due_date
                    ORDER BY th.id DESC
                    LIMIT 1
                ),
                return_date = (
                    SELECT th.return_date
                    FROM transaction_history th
                    WHERE th.book_code = (
                        SELECT b.book_code
                        FROM books b
                        WHERE b.id = book_transactions.book_id
                    )
                    AND th.employee_code = (
                        SELECT e.employee_code
                        FROM employees e
                        WHERE e.id = book_transactions.employee_id
                    )
                    AND th.issue_date = book_transactions.issue_date
                    AND th.due_date = book_transactions.due_date
                    ORDER BY th.id DESC
                    LIMIT 1
                )
            """
        )
    )

    # ---------------------------------------------------------
    # 3. Make status NOT NULL again
    # ---------------------------------------------------------
    with op.batch_alter_table(
        "book_transactions",
        schema=None
    ) as batch_op:
        batch_op.alter_column(
            "status",
            existing_type=sa.String(length=20),
            nullable=False
        )

    # ---------------------------------------------------------
    # 4. Remove transaction history
    # ---------------------------------------------------------
    op.drop_table("transaction_history")