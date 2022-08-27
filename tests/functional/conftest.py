import pytest

from src.services.jira import JiraSvc
from src.settings.env import env, load_dotenv


@pytest.fixture(scope="module")
def svc(app):
    load_dotenv(True)
    svc = JiraSvc(
        url=env.str("CI_JIRA_CLOUD_URL"),
        user=env.str("CI_JIRA_CLOUD_USER"),
        token=env.str("CI_JIRA_CLOUD_TOKEN"),
    )
    return svc
