import os
import tempfile
import pytest
from tassaron_flask_template.main import create_app, init_app
from tassaron_flask_template.main.plugins import plugins
from tassaron_flask_template.main.models import User
from tassaron_flask_template.main.routes import all_base_urls


@pytest.fixture
def client():
    global app, db, bcrypt, login_manager
    app = create_app()
    db, migrate, bcrypt, login_manager = plugins
    db_fd, db_path = tempfile.mkstemp()
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite+pysqlite:///" + db_path
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["TESTING"] = True
    app = init_app(app)
    client = app.test_client()
    with app.app_context():
        with client:
            db.create_all()
            user = User(email="test@example.com", password="password", is_admin=True)
            db.session.add(user)
            db.session.commit()
            client.post(
                "/account/login",
                data={"email": "test@example.com", "password": "password"},
                follow_redirects=True,
            )
            yield client
    os.close(db_fd)
    os.unlink(db_path)


def test_admin_privilege(client):
    resp = client.get(app.config["ADMIN_URL"])
    assert resp.status_code == 200


def test_all_admin_routes(client):
    endpoints = [url for url in all_base_urls() if url.startswith(app.config["ADMIN_URL"])]
    endpoints.remove(app.config["ADMIN_URL"])
    for endpoint in endpoints:
        resp = client.get(endpoint)
        assert resp.status_code == 200