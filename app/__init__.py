import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["300 per hour"],
    storage_uri="memory://",
)


def create_app(test_config=None):
    app = Flask(__name__, template_folder="templates", static_folder="static")

    db_path = os.getenv("SQLITE_PATH") or os.path.join("/tmp", "payflow-upi.db")

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "payflow-dev-secret-change-in-production")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{db_path}",
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}
    app.config["WTF_CSRF_TIME_LIMIT"] = None

    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"

    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.account import account_bp
    from app.routes.transaction import transaction_bp
    from app.routes.beneficiary import beneficiary_bp
    from app.routes.reports import reports_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(account_bp)
    app.register_blueprint(transaction_bp)
    app.register_blueprint(beneficiary_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        from app import models  # noqa: F401
        db.create_all()

    @app.template_filter("inr")
    def inr(value):
        try:
            n = float(value)
        except (TypeError, ValueError):
            return "₹0.00"
        return f"₹{n:,.2f}"

    return app
