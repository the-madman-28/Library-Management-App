# from app import create_app


# app = create_app()


# if __name__ == "__main__":
#     app.run(debug=True)


from sqlalchemy import text

from app import create_app
from app.extensions import db


app = create_app()


# Temporary database diagnostic for Vercel deployment.
# Remove this block after the database issue is resolved.
try:
    with app.app_context():
        database_info = db.session.execute(
            text("""
                SELECT
                    current_database(),
                    current_schema(),
                    current_user
            """)
        ).fetchone()

        users_columns = db.session.execute(
            text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = current_schema()
                  AND table_name = 'users'
                ORDER BY ordinal_position
            """)
        ).scalars().all()

        print("=== DATABASE DIAGNOSTIC ===")
        print("DATABASE :", database_info[0])
        print("SCHEMA   :", database_info[1])
        print("USER     :", database_info[2])
        print("USERS COLUMNS :", users_columns)
        print("============================")

except Exception as exc:
    print("=== DATABASE DIAGNOSTIC ERROR ===")
    print(repr(exc))
    print("=================================")


if __name__ == "__main__":
    app.run(debug=True)