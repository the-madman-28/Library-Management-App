"""Add library to users

Revision ID: c293e4e40f5f
Revises: 626743133944
Create Date: 2026-10-10 11:10:37.050795

"""

from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c293e4e40f5f"
down_revision = "626743133944"
branch_labels = None
depends_on = None


def upgrade():
    # ---------------------------------------------------------
    # 1. Add library_id as nullable temporarily
    # ---------------------------------------------------------
    op.add_column(
        "users",
        sa.Column(
            "library_id",
            sa.Integer(),
            nullable=True
        )
    )

    # ---------------------------------------------------------
    # 2. Create a default library for existing users
    # ---------------------------------------------------------
    libraries_table = sa.table(
        "libraries",
        sa.column("id", sa.Integer()),
        sa.column("name", sa.String()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True))
    )

    now = datetime.now(timezone.utc)

    op.bulk_insert(
        libraries_table,
        [
            {
                "name": "Default Library",
                "created_at": now,
                "updated_at": now
            }
        ]
    )

    # ---------------------------------------------------------
    # 3. Get the ID of the default library
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

    # ---------------------------------------------------------
    # 4. Assign all existing users to Default Library
    # ---------------------------------------------------------
    connection.execute(
        sa.text(
            """
            UPDATE users
            SET library_id = :library_id
            WHERE library_id IS NULL
            """
        ),
        {
            "library_id": default_library_id
        }
    )

    # ---------------------------------------------------------
    # 5. Make library_id NOT NULL
    # ---------------------------------------------------------
    op.alter_column(
        "users",
        "library_id",
        existing_type=sa.Integer(),
        nullable=False
    )

    # ---------------------------------------------------------
    # 6. Add foreign key constraint
    # ---------------------------------------------------------
    op.create_foreign_key(
        "fk_users_library_id",
        "users",
        "libraries",
        ["library_id"],
        ["id"]
    )


def downgrade():
    # ---------------------------------------------------------
    # 1. Remove foreign key
    # ---------------------------------------------------------
    op.drop_constraint(
        "fk_users_library_id",
        "users",
        type_="foreignkey"
    )

    # ---------------------------------------------------------
    # 2. Remove library_id
    # ---------------------------------------------------------
    op.drop_column(
        "users",
        "library_id"
    )