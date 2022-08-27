from tests.functional.conftest import JiraTestCase


class TestJiraSvc(JiraTestCase):
    def test_exists_issue(self):
        issue = self.svc.create_issue(
            summary="Some dummy issue",
            project=self.project.key,
            issuetype=self.issue_type,
        )  # create dummy issue

        assert self.svc.exists_issue(issue.id)
        issue.delete()
        assert not self.svc.exists_issue(issue.id)
        assert not self.svc.exists_issue("000")
