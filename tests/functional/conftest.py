import pytest
import unittest

from src.app import create_app
from src.services.jira import JiraSvc
from src.settings.env import env, load_dotenv


@pytest.fixture(scope="module")
def app():
    app = create_app(
        config_name="testing",
        dotenv=True,
        configs={
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "FLASK_RUN_HOST": "localhost",
            "FLASK_RUN_PORT": 5000,
            "APPLICATION_ROOT": "/",
            "OPENAPI": "3.0.3",  # default version
            "JIRA_BOARDS": ["JIRA_CI_BOARD"],
            "JIRA_CI_BOARD": "CI board",
            "JIRA_DEFAULT_BOARD": "JIRA_CI_BOARD",
        },
    )
    with app.test_request_context():
        yield app


@pytest.fixture(scope="class")
def svc(app, request):
    svc = JiraSvc(
        url=env.str("JIRA_CLOUD_CI_URL"),
        user=env.str("JIRA_CLOUD_CI_USER"),
        token=env.str("JIRA_CLOUD_CI_TOKEN"),
    )
    request.cls.svc = svc
    return svc


@pytest.mark.usefixtures("svc")
class JiraTestCase(unittest.TestCase):
    def setUp(self):
        self.project = self.svc.project(env.str("JIRA_CLOUD_CI_PROJECT_KEY"))
        self.board = next(iter(self.svc.boards()))
        self.issue_type = env.str("JIRA_CLOUD_CI_ISSUE_TYPE")
