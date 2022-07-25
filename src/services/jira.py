import base64
import functools
import re
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
                "rest_api_version": 2,
                "agile_rest_path": jira.resources.AgileResource.AGILE_BASE_REST_PATH,
                "agile_rest_api_version": "latest",
            },
            **kwargs,
        )

    def content(
        self,
        path: str,
        params: typing.Optional[str] = None,
        base: typing.Optional[str] = None,
    ) -> bytes:
        """Get content bytes for a given path and params.

        :param path: sub-path required
        :param params: parameters to filter the json query.
        :param base: base Jira URL, defaults to the instance base.
        """
        url = self._get_url(path, base or self.JIRA_BASE_URL)
        return self._session.get(url, params=params).content

    def exists_issue(self, issue_id) -> bool:
        try:
            self.issue(id=issue_id)
        except jira.exceptions.JIRAError as ex:
            if ex.status_code == requests.codes.not_found:
                return False
        else:
            return True

    def has_permissions(self, permissions: list[str], **kwargs) -> bool:
        perms = self.my_permissions(permissions=",".join(permissions), **kwargs)
        return all(perms["permissions"][p]["havePermission"] for p in permissions)

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

    def board_filter(self, board_id):
        """Get the filter from a board's configuration

        :param board_id: the Jira id of the board
        :return: the board filter
        """
        configuration = self.board_configuration(board_id=board_id)
        return self.filter(configuration["filter"]["id"])

    def create_jql_query(
        self,
        assignee: str = None,
        filters: list[str] = None,
        expand: list[str] = None,
        key: typing.Union[str, list[str]] = None,
        labels: list[str] = None,
        sort: str = None,
        status: str = None,
        summary: str = None,
        tags: list[str] = None,
        watcher: str = None,
        **_,
    ):
        """Build jql query based on a provided searching parameters.

        :param assignee: the assignee key (e.g. email)
        :param filters: the filter ids to apply
        :param expand: the expand fields (enum: ['renderedFields'])
        :param key: the Jira ticket key
        :param labels: base labels to search for
        :param sort: sorting criteria (enum: ['created'])
        :param status: the status key
        :param summary: the text search
        :param tags: ticket categorization
        :param watcher: the watcher key (e.g. email)
        """
        jql = ""
        if filters:
            jql = f"{jql}&filter in ({', '.join(filters)})"
        if summary:
            jql = f"{jql}&summary ~ '{summary}'"
        if key:
            joined_keys = ", ".join(key) if isinstance(key, list) else key
            jql = f"{jql}&key in ({joined_keys})"
        if assignee:
            jql = f"{jql}&assignee={assignee}"
        if status:
            jql = f"{jql}&status='{status}'"
        if labels:
            for label in labels:
                jql = f"{jql}&labels={label}"
        if tags:
            joined_tags = ", ".join(tags)
            jql = f"{jql}&labels in ({joined_tags})"
        if watcher:
            jql = f"{jql}&watcher=" + watcher
        if expand:
            jql = f"{jql}&expand={','.join(expand)}"
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

    def __init__(self, **kwargs):
        super().__init__(
            url=current_app.config["ATLASSIAN_URL"],
            user=current_app.config["ATLASSIAN_USER"],
            token=current_app.config["ATLASSIAN_API_TOKEN"],
            **kwargs,
        )

    @functools.cache
    def boards(self) -> list[Board]:
        def from_env(envar):
            regex = r"^JIRA_|_BOARD$"
            return {"key": re.sub(regex, "", envar).lower(), "name": env(envar)}

        def make_board(v):
            name = v["name"]
            data = next((b for b in super().boards(name=name) if b.name == name), None)
            default = from_env(env(current_app.config["JIRA_DEFAULT_BOARD"]))
            return Board(key=v["key"], raw=data["raw"], is_default=(default == v))

        envs = [from_env(v) for v in current_app.config["JIRA_BOARDS"]]
        return [make_board(v) for v in envs]

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
            filters = [self.board_filter(board_id=b.id) for b in boards]
            kwargs["filters"] = (str(f.id) for f in filters)

        return super().create_jql_query(**kwargs)

    def add_attachment(
        self,
        issue: typing.Union[jira.Issue, str],
        attachment: typing.Union[
            werkzeug.datastructures.FileStorage, O365.message.MessageAttachment
        ],
        filename: str = None,
    ):
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
            super().add_attachment(
                issue=str(issue), attachment=content, filename=filename
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
