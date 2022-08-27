from tests.functional.conftest import JiraTestCase


class TestJiraSvc(JiraTestCase):
    def test_exists_issue(self):
        issue = self.svc.create_issue(
            summary="Some dummy issue",
            project=self.project.key,
            issuetype=self.issue_type,
        )  # create dummy issue

        assert self.svc.exists_issue(issue.id) is True
        issue.delete()
        assert self.svc.exists_issue(issue.id) is False
        assert self.svc.exists_issue("000") is False

    def test_has_permissions(self):
        assert self.svc.has_permissions(["BROWSE_PROJECTS", "CREATE_ISSUES"]) is True
        assert self.svc.has_permissions(["INVALID_PERMISSION"]) is False

    def test_board_configuration(self):
        print(self.svc.boards())
        assert False
