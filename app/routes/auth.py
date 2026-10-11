
import re

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

from email_validator import (
    validate_email,
    EmailNotValidError,
)

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

    # -----------------------------------------------------
    # REQUIRED FIELD VALIDATION
    # -----------------------------------------------------

    if not username or not password:
        flash(
            "Username and password are required.",
            "danger"
        )

        return redirect(
            url_for("main.index")
        )

    # -----------------------------------------------------
    # FIND USER
    # -----------------------------------------------------

    user = User.query.filter_by(
        username=username
    ).first()

    # -----------------------------------------------------
    # CHECK CREDENTIALS
    # -----------------------------------------------------

    if user is None or not user.check_password(password):
        flash(
            "Invalid username or password.",
            "danger"
        )

        return redirect(
            url_for("main.index")
        )

    # -----------------------------------------------------
    # CHECK ACCOUNT STATUS
    # -----------------------------------------------------

    if not user.is_active:
        flash(
            "Your account is inactive. Please contact an administrator.",
            "danger"
        )

        return redirect(
            url_for("main.index")
        )

    # -----------------------------------------------------
    # LOGIN
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # GET FORM DATA
    # -----------------------------------------------------

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

    # =====================================================
    # REQUIRED FIELD VALIDATION
    # =====================================================

    if not library_name:
        flash(
            "Library name is required.",
            "danger"
        )

        return redirect(
            url_for("main.index")
        )

    if not username:
        flash(
            "Username is required.",
            "danger"
        )

        return redirect(
            url_for("main.index")
        )

    if not email:
        flash(
            "Email address is required.",
            "danger"
        )

        return redirect(
            url_for("main.index")
        )

    if not password:
        flash(
            "Password is required.",
            "danger"
        )

        return redirect(
            url_for("main.index")
        )

    # =====================================================
    # LIBRARY NAME VALIDATION
    # =====================================================

    if len(library_name) < 2:
        flash(
            "Library name must contain at least 2 characters.",
            "danger"
        )

        return redirect(
            url_for("main.index")
        )

    if len(library_name) > 150:
        flash(
            "Library name must not exceed 150 characters.",
            "danger"
        )

        return redirect(
            url_for("main.index")
        )

    # Library name must contain at least one
    # letter or number.
    if not any(
        character.isalnum()
        for character in library_name
    ):
        flash(
            "Library name must contain at least one letter or number.",
            "danger"
        )

        return redirect(
            url_for("main.index")
        )

    # =====================================================
    # USERNAME VALIDATION
    # =====================================================

    if len(username) < 3:
        flash(
            "Username must be at least 3 characters long.",
            "danger"
        )

        return redirect(
            url_for("main.index")
        )

    if len(username) > 30:
        flash(
            "Username must not exceed 30 characters.",
            "danger"
        )

        return redirect(
            url_for("main.index")
        )

    # Only letters, numbers and underscores are allowed.
    if not re.fullmatch(
        r"[A-Za-z0-9_]+",
        username
    ):
        flash(
            "Username can contain only letters, numbers, and underscores.",
            "danger"
        )

        return redirect(
            url_for("main.index")
        )

    # =====================================================
    # EMAIL VALIDATION
    # =====================================================

    try:

        validated_email = validate_email(
            email,
            check_deliverability=False
        )

        email = validated_email.normalized

    except EmailNotValidError:

        # Keep the message simple and user-friendly.
        flash(
            "Please enter a valid email address, "
            "for example: someone@example.com.",
            "danger"
        )

        return redirect(
            url_for("main.index")
        )

    # =====================================================
    # PASSWORD VALIDATION
    # =====================================================

    password_errors = []

    # Minimum length
    if len(password) < 8:
        password_errors.append(
            "at least 8 characters"
        )

    # Maximum length
    if len(password) > 128:
        password_errors.append(
            "no more than 128 characters"
        )

    # Uppercase
    if not re.search(
        r"[A-Z]",
        password
    ):
        password_errors.append(
            "at least one uppercase letter"
        )

    # Lowercase
    if not re.search(
        r"[a-z]",
        password
    ):
        password_errors.append(
            "at least one lowercase letter"
        )

    # Number
    if not re.search(
        r"\d",
        password
    ):
        password_errors.append(
            "at least one number"
        )

    # Special character
    if not re.search(
        r"[^A-Za-z0-9]",
        password
    ):
        password_errors.append(
            "at least one special character"
        )

    # -----------------------------------------------------
    # DISPLAY ALL PASSWORD ERRORS AT ONCE
    # -----------------------------------------------------

    if password_errors:

        requirements = "; ".join(
            password_errors
        )

        flash(
            f"Password must contain {requirements}.",
            "danger"
        )

        return redirect(
            url_for("main.index")
        )

    # =====================================================
    # CHECK EXISTING USERNAME
    # =====================================================

    existing_username = User.query.filter_by(
        username=username
    ).first()

    if existing_username:
        flash(
            "Username is already in use. Please choose another username.",
            "danger"
        )

        return redirect(
            url_for("main.index")
        )

    # =====================================================
    # CHECK EXISTING EMAIL
    # =====================================================

    existing_email = User.query.filter_by(
        email=email
    ).first()

    if existing_email:
        flash(
            "This email address is already registered. "
            "Please use another email address.",
            "danger"
        )

        return redirect(
            url_for("main.index")
        )

    # =====================================================
    # CHECK EXISTING LIBRARY NAME
    # =====================================================

    existing_library = Library.query.filter_by(
        name=library_name
    ).first()

    if existing_library:
        flash(
            "A library with this name already exists. "
            "Please choose another library name.",
            "danger"
        )

        return redirect(
            url_for("main.index")
        )

    # =====================================================
    # CREATE LIBRARY + FIRST OWNER
    # =====================================================

    library = None
    user = None

    try:

        # -------------------------------------------------
        # CREATE LIBRARY
        # -------------------------------------------------

        library = Library(
            name=library_name
        )

        db.session.add(library)

        # Generate library.id before creating the user.
        db.session.flush()

        # -------------------------------------------------
        # CREATE FIRST USER / OWNER
        # -------------------------------------------------

        user = User(
            library_id=library.id,
            username=username,
            email=email,
            role="owner",
            is_active=True,
        )

        user.set_password(password)

        db.session.add(user)

        # -------------------------------------------------
        # SAVE EVERYTHING
        # -------------------------------------------------

        db.session.commit()

    # -----------------------------------------------------
    # DATABASE INTEGRITY ERROR
    # -----------------------------------------------------

    except IntegrityError:

        db.session.rollback()

        flash(
            "The library, username, or email is already in use.",
            "danger"
        )

        return redirect(
            url_for("main.index")
        )

    # -----------------------------------------------------
    # UNEXPECTED ERROR
    # -----------------------------------------------------

    except Exception:

        db.session.rollback()

        flash(
            "Unable to create the library. Please try again.",
            "danger"
        )

        return redirect(
            url_for("main.index")
        )

    # =====================================================
    # LOG IN THE NEW OWNER
    # =====================================================

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