from decimal import Decimal
import pytest
from app import create_app, db
from app.seed import seed
from app.models.user import User
from app.utils.transaction_helpers import perform_transfer


@pytest.fixture
def app():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test",
        }
    )
    with app.app_context():
        db.create_all()
        seed(force=True)
        yield app
        db.drop_all()


def test_successful_transfer(app):
    with app.app_context():
        rahul = User.query.filter_by(email="rahul@gmail.com").first()
        before = Decimal(rahul.total_balance)
        result = perform_transfer(rahul, "priya@hdfc", Decimal("100.00"), "test", "1234")
        assert result["success"] is True
        db.session.refresh(rahul)
        assert Decimal(rahul.total_balance) == before - Decimal("100.00")


def test_bad_pin(app):
    with app.app_context():
        rahul = User.query.filter_by(email="rahul@gmail.com").first()
        result = perform_transfer(rahul, "priya@hdfc", Decimal("10.00"), "x", "0000")
        assert result["success"] is False
        assert "PIN" in result["message"]


def test_insufficient_balance(app):
    with app.app_context():
        rahul = User.query.filter_by(email="rahul@gmail.com").first()
        result = perform_transfer(rahul, "priya@hdfc", Decimal("999999.00"), "x", "1234")
        assert result["success"] is False
        assert "Insufficient" in result["message"]
