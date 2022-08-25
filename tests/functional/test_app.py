import pytest

from src.app import create_app


@pytest.fixture(scope="class")
def local_app():
    app = create_app(
        config_name="testing",
        dotenv=False,
        configs={
            "FLASK_RUN_HOST": "localhost",
            "FLASK_RUN_PORT": 5000,
            "APPLICATION_ROOT": "/test/v1",
        },
    )
    with app.app_context():
        yield app


class TestApp:
    def test_can_create_app(self, app):
        """Ensure app is created."""
        assert app is not None

    def test_root_path(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_swagger_apidocs(self, client):
        """Ensure app serves swagger specs."""
        response = client.get("/specs.json")
        assert response.status_code == 200

    def test_url_application_root(self, local_app):
        """Ensure root path is redirected to application root."""
        client = local_app.test_client()

        response = client.get("/")
        assert response.status_code == 302

        response = client.get("/", follow_redirects=True)
        request = response.request
        assert response.status_code == 200
        assert request.path.rstrip("/") == "/test/v1"

        response = client.get("/test/v1/specs.json")
        assert response.status_code == 200
