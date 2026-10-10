from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
)

from flask_login import login_required, current_user
from sqlalchemy import or_

from app.extensions import db
from app.models import Book, BookTransaction


books_bp = Blueprint(
    "books",
    __name__,
    url_prefix="/books",
)


# =========================================================
# BOOK LIST
# =========================================================

@books_bp.route("/")
@login_required
def list_books():

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

    books = query.order_by(
        Book.title.asc()
    ).all()

    return render_template(
        "books/list.html",
        books=books,
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

    books = query.order_by(
        Book.title.asc()
    ).all()

    return render_template(
        "books/overview.html",
        books=books,
        search_query=search_query,
    )


# =========================================================
# ADD BOOK
# =========================================================

@books_bp.route(
    "/add",
    methods=["GET", "POST"],
)
@login_required
def add_book():

    if request.method == "POST":

        book_code = request.form.get(
            "book_code",
            "",
        ).strip()

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

        total_copies = request.form.get(
            "total_copies",
            "1",
        ).strip()

        # -------------------------------------------------
        # REQUIRED FIELDS
        # -------------------------------------------------

        if not book_code or not title:

            flash(
                "Book code and title are required.",
                "danger",
            )

            return render_template(
                "books/add.html"
            )

        # -------------------------------------------------
        # TOTAL COPIES VALIDATION
        # -------------------------------------------------

        try:

            total_copies = int(
                total_copies
            )

        except ValueError:

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
        # DUPLICATE BOOK CODE
        # Only within the current library
        # -------------------------------------------------

        existing_book = Book.query.filter_by(
            library_id=current_user.library_id,
            book_code=book_code,
        ).first()

        if existing_book:

            flash(
                "A book with this code already exists.",
                "danger",
            )

            return render_template(
                "books/add.html"
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
            "Book added successfully.",
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

        book_code = request.form.get(
            "book_code",
            "",
        ).strip()

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

        total_copies = request.form.get(
            "total_copies",
            "1",
        ).strip()

        # -------------------------------------------------
        # REQUIRED FIELDS
        # -------------------------------------------------

        if not book_code or not title:

            flash(
                "Book code and title are required.",
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

            total_copies = int(
                total_copies
            )

        except ValueError:

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
        # DUPLICATE BOOK CODE
        # Only within the current library
        # -------------------------------------------------

        existing_book = Book.query.filter(
            Book.library_id == current_user.library_id,
            Book.book_code == book_code,
            Book.id != book.id,
        ).first()

        if existing_book:

            flash(
                "Another book with this code already exists.",
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
        # -------------------------------------------------

        book.book_code = book_code
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

    search_query = request.args.get(
        "q",
        "",
    ).strip()

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

    books = query.order_by(
        Book.title.asc()
    ).all()

    return render_template(
        "books/available.html",
        books=books,
        search_query=search_query,
    )