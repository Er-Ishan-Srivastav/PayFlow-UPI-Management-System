import pytest
from app import create_app, db
from app.seed import seed


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


@pytest.fixture
def client(app):
    return app.test_client()


def test_login_page(client):
    rv = client.get("/login")
    assert rv.status_code == 200
    assert b"PayFlow" in rv.data


def test_login_success(client):
    rv = client.post(
        "/login",
        data={"login": "rahul@gmail.com", "password": "1234"},
        follow_redirects=True,
    )
    assert rv.status_code == 200
    assert b"Send money" in rv.data


def test_login_fail(client):
    rv = client.post("/login", data={"login": "rahul@gmail.com", "password": "nope"})
    assert b"Invalid" in rv.data
