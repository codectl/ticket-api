import io
import tempfile

import jira
import O365
import pytest
import werkzeug.datastructures

from tests.functional.conftest import JiraTestCase


@pytest.fixture
def issue(svc, board, issue_type, request):
    issue = svc.create_issue(
        summary="Some dummy issue",
        project=board.project,
        issuetype=issue_type,
    )
    request.cls.issue = issue
    return issue


class TestJiraSvc(JiraTestCase):
    @pytest.mark.usefixtures("issue")
    def test_exists_issue(self):
        assert self.svc.exists_issue(self.issue.id) is True
        self.issue.delete()
        assert self.svc.exists_issue(self.issue.id) is False
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

    def test_boards(self):
        boards = self.svc.boards()
        assert len(boards) == 1
        assert boards[0].name == "CI board"
        assert boards[0].is_default is True

    def test_jql_query(self):
        boards = self.svc.boards()
        query = self.svc.create_jql_query(board_keys=(board.key for board in boards))
        assert "filter in" in query

    @pytest.mark.usefixtures("issue")
    def test_add_attachment_file_storage(self):
        file = werkzeug.datastructures.FileStorage(
            stream=io.BytesIO(b"some dummy data"),
            filename="dummy.txt",
            content_type="text/plain",
        )
        attachment = self.svc.add_attachment(issue=self.issue, attachment=file)
        issue = self.svc.issue(id=self.issue.id)
        assert len(issue.fields.attachment) == 1
        assert issue.fields.attachment[0].id == attachment.id
        assert self.svc.attachment(id=attachment.id).get() == b"some dummy data"
        issue.delete()

    @pytest.mark.usefixtures("issue")
    def test_add_o365_attachment(self):
        protocol = O365.MSGraphProtocol()  # dummy protocol
        file = tempfile.NamedTemporaryFile()
        file.write(b"some dummy data")
        file.seek(0)
        file = O365.message.MessageAttachment(protocol=protocol, attachment=file.name)
        attachment = self.svc.add_attachment(issue=self.issue, attachment=file)
        issue = self.svc.issue(id=self.issue.id)
        assert len(issue.fields.attachment) == 1
        assert issue.fields.attachment[0].id == attachment.id
        assert self.svc.attachment(id=attachment.id).get() == b"some dummy data"
        issue.delete()
