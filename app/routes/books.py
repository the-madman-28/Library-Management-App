
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
)

from flask_login import login_required, current_user
from sqlalchemy import or_

from app.extensions import db
from app.models import Book, BookTransaction
from app.services.isbn import ISBNValidationError, normalize_isbn
from app.services.book_metadata import lookup_book_metadata


books_bp = Blueprint(
    "books",
    __name__,
    url_prefix="/books",
)


# =========================================================
# AUTOMATIC BOOK CODE GENERATOR
# Generates codes independently for each library.
# Example: B-001, B-002, B-003
# =========================================================

def generate_book_code(library_id):
    """Generate the next available Book Code for a library."""

    existing_codes = db.session.query(
        Book.book_code
    ).filter(
        Book.library_id == library_id,
        Book.book_code.like("B-%"),
    ).all()

    highest_number = 0

    for (code,) in existing_codes:
        if not code:
            continue

        prefix, separator, suffix = code.rpartition("-")

        if prefix == "B" and separator and suffix.isdigit():
            highest_number = max(
                highest_number,
                int(suffix),
            )

    return f"B-{highest_number + 1:03d}"


# =========================================================
# BOOK LIST
# =========================================================

@books_bp.route("/")
@login_required
def list_books():
    search_query = request.args.get("q", "").strip()
    library_id = current_user.library_id

    query = Book.query.filter_by(library_id=library_id)

    if search_query:
        search = f"%{search_query}%"
        query = query.filter(
            or_(
                Book.book_code.ilike(search),
                Book.title.ilike(search),
                Book.author.ilike(search),
                Book.publisher.ilike(search),
                Book.category.ilike(search),
                Book.isbn.ilike(search),
            )
        )

    # Pagination settings
    page = request.args.get("page", 1, type=int)
    per_page = 10

    pagination = query.order_by(
        Book.title.asc()
    ).paginate(
        page=page,
        per_page=per_page,
        error_out=False,
    )

    # Only current page books
    books = pagination.items

    return render_template(
        "books/list.html",
        books=books,
        pagination=pagination,
        search_query=search_query,
    )


# =========================================================
# BOOK OVERVIEW
# Read-only page used by dashboard
# =========================================================

@books_bp.route("/overview")
@login_required
def books_overview():

    search_query = request.args.get(
        "q",
        "",
    ).strip()

    library_id = current_user.library_id

    query = Book.query.filter_by(
        library_id=library_id
    )

    if search_query:
        search = f"%{search_query}%"

        query = query.filter(
            or_(
                Book.book_code.ilike(search),
                Book.title.ilike(search),
                Book.author.ilike(search),
                Book.publisher.ilike(search),
                Book.category.ilike(search),
                Book.isbn.ilike(search),
            )
        )

    page = request.args.get("page", 1, type=int)
    per_page = 10

    pagination = query.order_by(
        Book.title.asc()
    ).paginate(
        page=page,
        per_page=per_page,
        error_out=False,
    )

    return render_template(
        "books/overview.html",
        books=pagination.items,
        pagination=pagination,
        search_query=search_query,
    )


# =========================================================
# ISBN METADATA LOOKUP
# =========================================================

@books_bp.route("/lookup-isbn", methods=["POST"])
@login_required
def lookup_isbn():
    """Fetch book metadata without saving anything to the database."""

    payload = request.get_json(silent=True) or {}
    isbn = payload.get("isbn", "")

    if not isinstance(isbn, str) or not isbn.strip():
        return jsonify({
            "found": False,
            "message": "Please enter an ISBN first.",
        }), 400

    try:
        result = lookup_book_metadata(isbn.strip())

    except ISBNValidationError as exc:
        return jsonify({
            "found": False,
            "message": str(exc),
        }), 400

    except Exception:
        # Do not expose internal errors or API credentials to the client.
        return jsonify({
            "found": False,
            "message": (
                "Unable to look up book details right now. "
                "Please enter the details manually."
            ),
        }), 500

    return jsonify(result), 200


# =========================================================
# ADD BOOK
# Book Code is generated automatically.
# =========================================================

@books_bp.route(
    "/add",
    methods=["GET", "POST"],
)
@login_required
def add_book():

    if request.method == "POST":

        title = request.form.get(
            "title",
            "",
        ).strip()

        author = request.form.get(
            "author",
            "",
        ).strip()

        publisher = request.form.get(
            "publisher",
            "",
        ).strip()

        category = request.form.get(
            "category",
            "",
        ).strip()

        isbn = request.form.get(
            "isbn",
            "",
        ).strip()

        if isbn:
            try:
                isbn = normalize_isbn(isbn)
            except ISBNValidationError as exc:
                flash(str(exc), "danger")
                return render_template("books/add.html")
        # -------------------------------------------------
        # PREVENT DUPLICATE ISBN IN THE SAME LIBRARY
        # -------------------------------------------------

        if isbn:
            existing_book = Book.query.filter_by(
                library_id=current_user.library_id,
                isbn=isbn,
            ).first()

            if existing_book:
                flash(
                    "This book already exists in your library. "
                    "Please edit the existing book to increase its copies.",
                    "warning",
                )

                return render_template(
                    "books/add.html",
                    existing_book=existing_book,
                )
        total_copies = request.form.get(
            "total_copies",
            "1",
        ).strip()

        # -------------------------------------------------
        # REQUIRED FIELDS
        # -------------------------------------------------

        if not title:
            flash(
                "Book title is required.",
                "danger",
            )

            return render_template(
                "books/add.html"
            )

        # -------------------------------------------------
        # TOTAL COPIES VALIDATION
        # -------------------------------------------------

        try:
            total_copies = int(total_copies)

        except (ValueError, TypeError):
            flash(
                "Total copies must be a valid number.",
                "danger",
            )

            return render_template(
                "books/add.html"
            )

        if total_copies < 1:
            flash(
                "Total copies must be at least 1.",
                "danger",
            )

            return render_template(
                "books/add.html"
            )

        # -------------------------------------------------
        # GENERATE BOOK CODE AUTOMATICALLY
        # -------------------------------------------------

        book_code = generate_book_code(
            current_user.library_id
        )

        # -------------------------------------------------
        # CREATE BOOK
        # -------------------------------------------------

        book = Book(
            library_id=current_user.library_id,
            book_code=book_code,
            title=title,
            author=author or None,
            publisher=publisher or None,
            category=category or None,
            isbn=isbn or None,
            total_copies=total_copies,
            available_copies=total_copies,
        )

        db.session.add(book)
        db.session.commit()

        flash(
            f"Book added successfully. Book Code: {book_code}",
            "success",
        )

        return redirect(
            url_for("books.list_books")
        )

    return render_template(
        "books/add.html"
    )


# =========================================================
# EDIT BOOK
# Book Code is generated once and cannot be edited here.
# =========================================================

@books_bp.route(
    "/<int:book_id>/edit",
    methods=["GET", "POST"],
)
@login_required
def edit_book(book_id):

    # IMPORTANT:
    # Only retrieve a book belonging to the
    # currently logged-in user's library.

    book = Book.query.filter_by(
        id=book_id,
        library_id=current_user.library_id,
    ).first_or_404()

    if request.method == "POST":

        title = request.form.get(
            "title",
            "",
        ).strip()

        author = request.form.get(
            "author",
            "",
        ).strip()

        publisher = request.form.get(
            "publisher",
            "",
        ).strip()

        category = request.form.get(
            "category",
            "",
        ).strip()

        isbn = request.form.get(
            "isbn",
            "",
        ).strip()

        if isbn:
            try:
                isbn = normalize_isbn(isbn)
            except ISBNValidationError as exc:
                flash(str(exc), "danger")
                return render_template(
                    "books/edit.html",
                    book=book,
                )

        total_copies = request.form.get(
            "total_copies",
            "1",
        ).strip()

        # -------------------------------------------------
        # REQUIRED FIELDS
        # -------------------------------------------------

        if not title:
            flash(
                "Book title is required.",
                "danger",
            )

            return render_template(
                "books/edit.html",
                book=book,
            )

        # -------------------------------------------------
        # TOTAL COPIES VALIDATION
        # -------------------------------------------------

        try:
            total_copies = int(total_copies)

        except (ValueError, TypeError):
            flash(
                "Total copies must be a valid number.",
                "danger",
            )

            return render_template(
                "books/edit.html",
                book=book,
            )

        if total_copies < 1:
            flash(
                "Total copies must be at least 1.",
                "danger",
            )

            return render_template(
                "books/edit.html",
                book=book,
            )

        # -------------------------------------------------
        # CURRENTLY ISSUED COPIES
        # -------------------------------------------------

        issued_copies = (
            book.total_copies -
            book.available_copies
        )

        # -------------------------------------------------
        # CANNOT REDUCE BELOW ISSUED COPIES
        # -------------------------------------------------

        if total_copies < issued_copies:
            flash(
                f"Total copies cannot be less than the "
                f"{issued_copies} currently issued copy/copies.",
                "danger",
            )

            return render_template(
                "books/edit.html",
                book=book,
            )

        # -------------------------------------------------
        # UPDATE BOOK
        # Book Code is deliberately left unchanged.
        # -------------------------------------------------

        book.title = title
        book.author = author or None
        book.publisher = publisher or None
        book.category = category or None
        book.isbn = isbn or None

        book.total_copies = total_copies

        book.available_copies = (
            total_copies -
            issued_copies
        )

        db.session.commit()

        flash(
            "Book updated successfully.",
            "success",
        )

        return redirect(
            url_for("books.list_books")
        )

    return render_template(
        "books/edit.html",
        book=book,
    )


# =========================================================
# DELETE BOOK
# =========================================================

@books_bp.route(
    "/<int:book_id>/delete",
    methods=["POST"],
)
@login_required
def delete_book(book_id):

    # IMPORTANT:
    # Prevent users from deleting books belonging
    # to another library.

    book = Book.query.filter_by(
        id=book_id,
        library_id=current_user.library_id,
    ).first_or_404()

    # -------------------------------------------------
    # BLOCK DELETE IF BOOK IS CURRENTLY ISSUED
    # -------------------------------------------------

    active_transaction = BookTransaction.query.filter_by(
        book_id=book.id,
        library_id=current_user.library_id,
    ).first()

    if active_transaction:
        flash(
            f"Cannot delete '{book.title}' because it is "
            f"currently issued and has not been returned.",
            "danger",
        )

        return redirect(
            url_for("books.list_books")
        )

    # -------------------------------------------------
    # DELETE BOOK
    # -------------------------------------------------

    db.session.delete(book)
    db.session.commit()

    flash(
        "Book deleted successfully.",
        "success",
    )

    return redirect(
        url_for("books.list_books")
    )


# =========================================================
# AVAILABLE BOOKS
# Read-only page used by dashboard
# =========================================================

@books_bp.route("/available")
@login_required
def available_books():

    search_query = request.args.get("q", "").strip()

    query = Book.query.filter(
        Book.library_id == current_user.library_id,
        Book.available_copies > 0,
    )

    if search_query:
        search = f"%{search_query}%"

        query = query.filter(
            or_(
                Book.book_code.ilike(search),
                Book.title.ilike(search),
                Book.author.ilike(search),
                Book.publisher.ilike(search),
                Book.category.ilike(search),
                Book.isbn.ilike(search),
            )
        )

    page = request.args.get("page", 1, type=int)
    per_page = 10

    pagination = query.order_by(
        Book.title.asc()
    ).paginate(
        page=page,
        per_page=per_page,
        error_out=False,
    )

    return render_template(
        "books/available.html",
        books=pagination.items,
        pagination=pagination,
        search_query=search_query,
    )
