from flask import (
    Blueprint,
    request,
    redirect,
    url_for,
    flash,
)
from flask_login import (
    login_user,
    logout_user,
    current_user,
)

from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import User, Library


auth_bp = Blueprint(
    "auth",
    __name__
)


# =========================================================
# LOGIN
# =========================================================

@auth_bp.route("/login", methods=["POST"])
def login():

    username = request.form.get(
        "username",
        ""
    ).strip()

    password = request.form.get(
        "password",
        ""
    )

    if not username or not password:
        flash(
            "Username and password are required.",
            "danger"
        )

        return redirect(
            url_for("main.index")
        )

    user = User.query.filter_by(
        username=username
    ).first()

    if user is None or not user.check_password(password):
        flash(
            "Invalid username or password.",
            "danger"
        )

        return redirect(
            url_for("main.index")
        )

    if not user.is_active:
        flash(
            "Your account is inactive. Please contact an administrator.",
            "danger"
        )

        return redirect(
            url_for("main.index")
        )

    login_user(user)

    return redirect(
        url_for("main.dashboard")
    )


# =========================================================
# REGISTER LIBRARY + FIRST OWNER
# =========================================================

@auth_bp.route("/register", methods=["POST"])
def register():

    # -----------------------------------------------------
    # PREVENT AUTHENTICATED USER FROM CREATING ANOTHER
    # LIBRARY THROUGH THE PUBLIC REGISTRATION FORM
    # -----------------------------------------------------

    if current_user.is_authenticated:
        return redirect(
            url_for("main.dashboard")
        )

    library_name = request.form.get(
        "library_name",
        ""
    ).strip()

    username = request.form.get(
        "username",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip().lower()

    password = request.form.get(
        "password",
        ""
    )

    # -----------------------------------------------------
    # BASIC VALIDATION
    # -----------------------------------------------------

    if not all([
        library_name,
        username,
        email,
        password
    ]):
        flash(
            "All fields are required.",
            "danger"
        )

        return redirect(
            url_for("main.index")
        )

    if len(password) < 8:
        flash(
            "Password must be at least 8 characters long.",
            "danger"
        )

        return redirect(
            url_for("main.index")
        )

    # -----------------------------------------------------
    # CHECK EXISTING USERNAME
    # -----------------------------------------------------

    existing_username = User.query.filter_by(
        username=username
    ).first()

    if existing_username:
        flash(
            "Username is already in use.",
            "danger"
        )

        return redirect(
            url_for("main.index")
        )

    # -----------------------------------------------------
    # CHECK EXISTING EMAIL
    # -----------------------------------------------------

    existing_email = User.query.filter_by(
        email=email
    ).first()

    if existing_email:
        flash(
            "Email is already registered.",
            "danger"
        )

        return redirect(
            url_for("main.index")
        )

    # -----------------------------------------------------
    # CHECK EXISTING LIBRARY NAME
    # -----------------------------------------------------

    existing_library = Library.query.filter_by(
        name=library_name
    ).first()

    if existing_library:
        flash(
            "A library with this name already exists.",
            "danger"
        )

        return redirect(
            url_for("main.index")
        )

    # -----------------------------------------------------
    # CREATE LIBRARY + FIRST OWNER
    # -----------------------------------------------------

    library = None
    user = None

    try:

        library = Library(
            name=library_name
        )

        db.session.add(library)

        # Generate library.id before creating the user.
        db.session.flush()

        user = User(
            library_id=library.id,
            username=username,
            email=email,
            role="owner",
            is_active=True,
        )

        user.set_password(password)

        db.session.add(user)

        db.session.commit()

    except IntegrityError:

        db.session.rollback()

        flash(
            "The library, username, or email is already in use.",
            "danger"
        )

        return redirect(
            url_for("main.index")
        )

    except Exception:

        db.session.rollback()

        flash(
            "Unable to create the library. Please try again.",
            "danger"
        )

        return redirect(
            url_for("main.index")
        )

    # -----------------------------------------------------
    # LOG IN THE NEW OWNER
    # -----------------------------------------------------

    login_user(user)

    flash(
        f"Welcome to {library.name}!",
        "success"
    )

    return redirect(
        url_for("main.dashboard")
    )


# =========================================================
# LOGOUT
# =========================================================

@auth_bp.route("/logout", methods=["POST"])
def logout():

    logout_user()

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(
        url_for("main.index")
    )