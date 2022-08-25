import pytest

from src.app import create_app


@pytest.fixture(scope="class")
def app():
    app = create_app(
        config_name="testing",
        dotenv=False,
        configs={
            "FLASK_RUN_HOST": "localhost",
            "FLASK_RUN_PORT": 5000,
            "APPLICATION_ROOT": "/",
            "OPENAPI": "3.0.3",  # default version
            "SUPPORTED_MEASURABLES": ["foo", "bar"],
        },
    )
    with app.test_request_context():
        yield app


@pytest.fixture(scope="class")
def client(app):
    return app.test_client()
