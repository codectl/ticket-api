import pytest
import unittest

from src.services.jira import JiraSvc
from src.settings.env import env, load_dotenv


@pytest.fixture(scope="class")
def svc(app, request):
    load_dotenv(True)
    svc = JiraSvc(
        url=env.str("CI_JIRA_CLOUD_URL"),
        user=env.str("CI_JIRA_CLOUD_USER"),
        token=env.str("CI_JIRA_CLOUD_TOKEN"),
    )
    request.cls.svc = svc
    return svc


@pytest.mark.usefixtures("svc")
class JiraTestCase(unittest.TestCase):
    def setUp(self):
        self.project = self.svc.project(env.str("CI_JIRA_CLOUD_PROJECT_KEY"))
        self.issue_type = env.str("CI_JIRA_ISSUE_TYPE")
