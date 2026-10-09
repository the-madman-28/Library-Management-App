from flask import Flask

from config import Config
from app.extensions import db, migrate


def create_app(config_class=Config):
    app = Flask(__name__)

    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    # Import all models so SQLAlchemy/Flask-Migrate knows about them
    from app.models import (
        User,
        Book,
        Employee,
        BookTransaction,
        TransactionHistory
    )

    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.books import books_bp
    from app.routes.employees import employees_bp
    from app.routes.transactions import transactions_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(books_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(transactions_bp)

    return app