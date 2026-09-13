import pytest
from app import create_app, db
from app.seed import seed
from app.models.user import User
from app.models.upi import UPIId


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


def test_five_demo_users(app):
    with app.app_context():
        assert User.query.count() == 5
        assert UPIId.query.filter_by(upi_address="rahul@sbi").first() is not None
