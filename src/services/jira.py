import base64
import functools
import io
import re
import tempfile
import typing

import jira.resources
import O365
import requests
import werkzeug.datastructures
from flask import current_app
from jira import JIRA

from src.models.jira import Board
from src.models.ticket import Ticket
from src.settings.env import env

__all__ = ("JiraSvc",)


class ProxyJIRA(JIRA):
    """Proxy class for Jira."""

    def __init__(self, **kwargs):
        url = kwargs.pop("url")
        user = kwargs.pop("user")
        token = kwargs.pop("token")
        super().__init__(
            server=url,
            basic_auth=(user, token),
            options={
                "rest_path": "api",
                "rest_api_version": 3,
                "agile_rest_path": jira.resources.AgileResource.AGILE_BASE_REST_PATH,
                "agile_rest_api_version": "latest",
            },
            **kwargs,
        )

    def exists_issue(self, issue_id) -> bool:
        try:
            self.issue(id=issue_id)
        except jira.exceptions.JIRAError as ex:
            if ex.status_code == requests.codes.not_found:
                return False
        else:
            return True

    def has_permissions(self, permissions: list[str], **kwargs) -> bool:
        try:
            data = self.my_permissions(permissions=",".join(permissions), **kwargs)
        except jira.JIRAError:
            return False
        else:
            return all(p in data["permissions"] for p in permissions) and all(
                data["permissions"][p]["havePermission"] for p in permissions
            )

    def my_permissions(
        self,
        project_key=None,
        project_id=None,
        issue_key=None,
        issue_id=None,
        permissions=None,
    ):
        """Override.

        :param project_key: see overridden method
        :param project_id: see overridden method
        :param issue_key: see overridden method
        :param issue_id: see overridden method
        :param permissions: limit returned permissions to the specified permissions.
                            Change introduce by Jira as per early 2020.
        """
        params = {}
        if project_key is not None:
            params["projectKey"] = project_key
        if project_id is not None:
            params["projectId"] = project_id
        if issue_key is not None:
            params["issueKey"] = issue_key
        if issue_id is not None:
            params["issueId"] = issue_id
        if permissions is not None:
            params["permissions"] = permissions
        return self._get_json("mypermissions", params=params)

    def board_configuration(self, board_id) -> dict:
        """Get the configuration from a given board

        :param board_id: the Jira id of the board
        :return: the board configuration
        """
        url = self._get_url(f"board/{board_id}/configuration", base=self.AGILE_BASE_URL)
        return self._session.get(url).json()

    @staticmethod
    def create_jql_query(
        assignee: str = None,
        filters: list[str] = None,
        expand: list[str] = None,
        key: typing.Union[str, list[str]] = None,
        labels: list[str] = None,
        status: str = None,
        summary: str = None,
        watcher: str = None,
        sort: str = None,
        **_,
    ):
        """Build jql query based on a provided searching parameters.

        :param assignee: the assignee key (e.g. email)
        :param expand: the expand fields (enum: ['renderedFields'])
        :param filters: the filter ids to apply
        :param key: the Jira ticket key
        :param labels: base labels to search for
        :param status: the status key
        :param summary: the text search
        :param watcher: the watcher key (e.g. email)
        :param sort: sorting criteria (enum: ['created'])
        """
        jql = ""
        if assignee:
            jql = f"{jql}&assignee={assignee}"
        if expand:
            jql = f"{jql}&expand={','.join(expand)}"
        if filters:
            jql = f"{jql}&filter in ({', '.join(filters)})"
        if key:
            joined_keys = ", ".join(key) if isinstance(key, list) else key
            jql = f"{jql}&key in ({joined_keys})"
        if labels:
            joined_labels = ", ".join(labels)
            jql = f"{jql}&labels in ({joined_labels})"
        if status:
            jql = f"{jql}&status='{status}'"
        if summary:
            jql = f"{jql}&summary ~ '{summary}'"
        if watcher:
            jql = f"{jql}&watcher=" + watcher
        if sort:
            jql = f"{jql} ORDER BY {sort}"

        # remove trailing url character
        jql = jql.lstrip("&")

        return jql

    @property
    def markdown(self):
        return JiraMarkdown(parent=self)


class JiraMarkdown(ProxyJIRA):
    def __init__(self, parent=None, **kwargs):
        if parent and isinstance(parent, ProxyJIRA):
            self.__dict__.update(parent.__dict__)
        else:
            super().__init__(**kwargs)

    @staticmethod
    def mention(user):
        """Create Jira markdown mention out of a user.

        If user does not exist, create email markdown.
        """
        if isinstance(user, jira.User):
            return f"[~accountid:{user.accountId}]"
        elif isinstance(user, str):
            return "".join(("[", user, ";|", "mailto:", user, "]"))
        else:
            return None


class JiraSvc(ProxyJIRA):
    """Service to handle Jira operations."""

    def __init__(
        self,
        url=None,
        user=None,
        token=None,
        **kwargs,
    ):
        url = url or current_app.config["ATLASSIAN_URL"]
        user = user or current_app.config["ATLASSIAN_USER"]
        token = token or current_app.config["ATLASSIAN_API_TOKEN"]
        super().__init__(
            url=url,
            user=user,
            token=token,
            **kwargs,
        )

    @functools.cache
    def boards(self) -> list[Board]:
        def from_config(var):
            regex = r"^JIRA_|_BOARD$"
            return {
                "key": re.sub(regex, "", var).lower(),
                "name": current_app.config.get(var, env(var)),
            }

        def make_board(conf):
            name = conf["name"]
            boards = super(ProxyJIRA, self).boards(name=name)
            board = next((board for board in boards if board.name == name), None)
            default = from_config(current_app.config["JIRA_DEFAULT_BOARD"])
            return Board(key=conf["key"], raw=board.raw, is_default=(default == conf))

        configs = [from_config(var) for var in current_app.config["JIRA_BOARDS"]]
        return [make_board(config) for config in configs]

    def create_jql_query(
        self,
        board_keys: list[str] = None,
        **kwargs,
    ):
        def find_board(key):
            return next(b for b in self.boards() if b.key == key)

        if board_keys:
            boards = [find_board(key=key) for key in board_keys]

            # translate boards into filters
            configs = [self.board_configuration(board_id=b.id) for b in boards]
            kwargs["filters"] = [config["filter"]["id"] for config in configs]

        return super().create_jql_query(**kwargs)

    def add_attachment(
        self,
        issue: typing.Union[jira.Issue, str],
        attachment: typing.Union[
            werkzeug.datastructures.FileStorage, O365.message.MessageAttachment
        ],
        filename: str = None,
    ) -> typing.Optional[jira.resources.Attachment]:
        """Add attachment considering different types of files."""
        content = None
        if isinstance(attachment, werkzeug.datastructures.FileStorage):
            filename = filename or attachment.filename
            content = attachment.stream.read()
        elif isinstance(attachment, O365.message.MessageAttachment):
            filename = filename or attachment.name
            if not attachment.content:
                current_app.logger.warning(f"Attachment '{filename}' is empty")
            else:
                content = base64.b64decode(attachment.content)
        else:
            msg = f"'{type(attachment)}' is not a supported attachment type."
            current_app.logger.warning(msg)

        # no point on adding empty file
        if content:
            file = tempfile.TemporaryFile()
            file.write(content)
            file.seek(0)
            fi = io.FileIO(file.fileno())
            return super().add_attachment(
                issue=str(issue),
                attachment=io.BufferedReader(fi),
                filename=filename,
            )

    def add_watchers(
        self, issue: typing.Union[Ticket, str], watchers: list[jira.User] = None
    ):
        """Add a list of watchers to a ticket.

        :param issue: the Jira issue
        :param watchers:
        """
        # add watchers iff has permission
        if self.has_permissions(permissions=["MANAGE_WATCHERS"], issue_key=str(issue)):
            for watcher in watchers or []:
                if isinstance(watcher, jira.User):
                    try:
                        self.add_watcher(issue=str(issue), watcher=watcher.accountId)
                    except jira.exceptions.JIRAError as e:
                        if e.status_code not in (
                            requests.codes.unauthorized,
                            requests.codes.forbidden,
                        ):
                            raise e
                        else:
                            name = watcher.displayName
                            current_app.logger.warning(
                                f"Watcher '{name}' has no permission to watch issue "
                                f"'{str(issue)}'."
                            )
        else:
            msg = "The 'me' user has no permission to manage watchers."
            current_app.logger.warning(msg)

    @staticmethod
    def is_jira_filter(filter_name):
        """Check whether given filter is a Jira only filter."""
        return filter_name in [
            "assignee",
            "boards",
            "category",
            "key",
            "q",
            "sort",
            "status",
            "watcher",
        ]

    @classmethod
    def default_board(cls):
        return next(b for b in cls().boards() if b.is_default)

    @staticmethod
    def allowed_categories():
        return current_app.config["JIRA_TICKET_LABEL_CATEGORIES"]

    @staticmethod
    def allowed_fields():
        return ["watchers", "comments", "attachments", "rendered"]
