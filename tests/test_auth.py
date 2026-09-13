import pytest
from app import create_app, db
from app.models.user import User

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
    })
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_register_page(client):
    rv = client.get('/auth/register')
    assert rv.status_code == 200

def test_login_page(client):
    rv = client.get('/auth/login')
    assert rv.status_code == 200
