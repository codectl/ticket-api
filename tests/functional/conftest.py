import pytest

from src.services.jira import JiraSvc
from src.settings.env import env


# @pytest.fixture(scope="module")
# def svc(app):
#     svc = JiraSvc(
#         url=env.str("CI_JIRA_CLOUD_URL"),
#         user=env.str("CI_JIRA_CLOUD_USER"),
#         token=env.str("CI_JIRA_CLOUD_TOKEN"),
#     )
#     return svc
