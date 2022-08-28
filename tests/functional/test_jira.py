import jira
import pytest

from tests.functional.conftest import JiraTestCase


class TestJiraSvc(JiraTestCase):
    def test_boards(self):
        boards = self.svc.boards()
        assert len(boards) == 1
        assert boards[0].name == "CI board"
        assert boards[0].is_default is True

    def test_jql_query(self):
        boards = self.svc.boards()
        query = self.svc.create_jql_query(board_keys=(board.key for board in boards))
        assert "filter in" in query

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
        config = self.svc.board_configuration(board_id=self.board.id)
        assert "filter" in config
        assert "location" in config
        with pytest.raises(jira.JIRAError) as ex:
            self.svc.board_configuration(board_id="000")
            ex.status_code = 404
