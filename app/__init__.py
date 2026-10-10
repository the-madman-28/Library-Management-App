from flask import Flask

from config import Config
from app.extensions import db, migrate, login_manager


def create_app(config_class=Config):
    app = Flask(__name__)

    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Import all models so SQLAlchemy/Flask-Migrate knows about them
    from app.models import (
        User,
        Book,
        Library,
        Employee,
        BookTransaction,
        TransactionHistory
    )

    # Flask-Login user loader
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.books import books_bp
    from app.routes.employees import employees_bp
    from app.routes.transactions import transactions_bp
    from app.routes.auth import auth_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(books_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(auth_bp)

    return app