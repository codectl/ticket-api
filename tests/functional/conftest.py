import pytest
import unittest

from src.app import create_app
from src.services.jira import JiraSvc


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
    svc = JiraSvc()
    request.cls.svc = svc
    return svc


@pytest.fixture(scope="class")
def board(app, svc, request):
    board = next(iter(svc.boards()))
    request.cls.board = board
    return board


@pytest.fixture(scope="class")
def issue_type(app, svc, request):
    issue_type = app.config["JIRA_TICKET_TYPE"]
    request.cls.issue_type = issue_type
    return issue_type


@pytest.mark.usefixtures("svc", "board", "issue_type")
class JiraTestCase(unittest.TestCase):

    def setUp(self) -> None:
        # add a guest user
        self.svc.add_user(username="guest", email="guest@example.com")
        self.guest_user = next(self.svc.search_users(query="guest"))
