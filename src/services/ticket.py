import os
import typing

import jinja2
import jira.resources
from flask import current_app

from src.models.ticket import Ticket
from src.services.jira import JiraSvc
from src.settings.ctx import db


class TicketSvc:
    @classmethod
    def create(cls, attachments: list = None, **kwargs) -> dict:
        """Create a new ticket by calling Jira API to create a new
        issue. A new local reference is also created.

        :param attachments: the files to attach to the ticket which
                            are stored in Jira
        :param kwargs: properties of the ticket
            title: title of the ticket
            description: body of the ticket
            reporter: email of the author's ticket
            board: board key which the ticket belongs to
            category: which category to assign ticket to
            priority: severity of the ticket
            watchers: user emails to watch for ticket changes
        """
        svc = JiraSvc()

        # translate emails into jira.User objects
        reporter = cls.resolve_email(email=kwargs.get("reporter"))
        watchers = [
            cls.resolve_email(email, default=email)
            for email in kwargs.get("watchers") or []
        ]

        # create ticket body with Jira markdown format
        body = cls.create_message_body(
            template="jira.j2",
            values={
                "author": svc.markdown.mention(user=reporter or kwargs.get("reporter")),
                "cc": " ".join(svc.markdown.mention(user=w) for w in watchers),
                "body": kwargs.get("body"),
            },
        )

        # if reporter is not a Jira account, reporter is set to 'Anonymous'
        reporter_id = getattr(reporter, "accountId", None)

        # set defaults
        board = next(b for b in svc.boards() if b.key == kwargs.get("board"))
        project_key = board.raw["location"]["projectKey"]
        priority = (kwargs.get("priority") or "").lower()
        priority = priority if priority in ["high", "low"] else "None"
        priority = {"name": priority.capitalize()}

        category = kwargs.pop("category")
        categories = category.split(",") + current_app.config["JIRA_TICKET_LABELS"]

        # create ticket in Jira
        issue = svc.create_issue(
            summary=kwargs.get("title"),
            description=body,
            reporter={"id": reporter_id},
            project={"key": project_key},
            issuetype={"name": current_app.config["JIRA_TICKET_TYPE"]},
            labels=categories,
            priority=priority,
        )

        # add watchers
        svc.add_watchers(issue=issue.key, watchers=watchers)

        # adding attachments
        for attachment in attachments or []:
            svc.add_attachment(issue=issue, attachment=attachment)

        # add new entry to the db
        local_fields = {k: v for k, v in kwargs.items() if k in Ticket.__dict__}
        ticket = Ticket(key=issue.key, **local_fields)

        db.session.add(ticket)
        db.session.commit()

        current_app.logger.info(f"Created ticket '{ticket.key}'.")

        return TicketSvc.find_one(key=ticket.key)

    @staticmethod
    def get(ticket_id) -> typing.Optional[Ticket]:
        return Ticket.query.get(ticket_id)

    @classmethod
    def find_one(cls, **filters) -> typing.Optional[typing.Union[dict, Ticket]]:
        """Search for a single ticket based on several criteria."""
        return next(iter(cls.find_by(limit=1, **filters)), None)

    @classmethod
    def find_by(
        cls, limit: int = 20, fields: list = None, _model: bool = False, **filters
    ) -> list[typing.Union[dict, Ticket]]:
        """Search for tickets based on several criteria.

        Jira's filters are also supported.

        :param limit: the max number of results retrieved
        :param fields: additional fields to include in results schema
        :param _model: whether to return a ticket model or cross results Jira data
        :param filters: the query filters
        """
        svc = JiraSvc()

        # split filters
        local_filters = {k: v for k, v in filters.items() if k in Ticket.__dict__}
        jira_filters = {k: v for k, v in filters.items() if svc.is_jira_filter(k)}

        if _model:
            return Ticket.query.filter_by(**local_filters).all()
        else:
            # if any of the filter is not a Jira filter, then
            # apply local filter and pass on results to jql
            if local_filters:
                tickets = Ticket.query.filter_by(**local_filters).all()

                # skip routine if no local entries are found
                if not tickets:
                    return []
                jira_filters["key"] = [ticket.key for ticket in tickets]

            # fetch tickets from Jira using jql while skipping jql
            # validation since local db might not be synched with Jira
            query = svc.create_jql_query(
                summary=filters.pop("q", None),
                labels=current_app.config["JIRA_TICKET_LABELS"],
                tags=filters.pop("categories", []),
                **jira_filters,
            )

            # include additional fields
            fields = fields or []
            if "*navigable" not in fields:
                fields.append("*navigable")
            rendered = "renderedFields" if "rendered" in fields else "fields"

            # remove plurals in fields
            issues = svc.search_issues(
                jql_str=query,
                maxResults=limit,
                validate_query=False,
                fields=",".join([f[:-1] if f.endswith("s") else f for f in fields]),
                expand=rendered,
            )

            tickets = []
            for issue in issues:
                model = cls.find_one(key=issue.key, _model=True)

                # prevent cases where local db is not synched with Jira
                # for cases where Jira tickets are not yet locally present
                if model:
                    url = current_app.config["ATLASSIAN_URL"]
                    ticket = issue.raw["fields"]
                    ticket["id"] = issue.id
                    ticket["key"] = issue.key
                    ticket["url"] = f"{url}/browse/{issue.key}"
                    ticket["reporter"] = {"emailAddress": model.reporter}

                    # add rendered fields if requested
                    if "rendered" in fields:
                        ticket["rendered"] = issue.raw["renderedFields"]

                    # add watchers if requested
                    if "watchers" in fields:
                        ticket["watchers"] = svc.watchers(issue.key).raw["watchers"]

                    tickets.append(ticket)
            return tickets

    @classmethod
    def update(cls, ticket_id, **kwargs):
        ticket = cls.get(ticket_id=ticket_id)
        for key, value in kwargs.items():
            if hasattr(ticket, key):
                setattr(ticket, key, value)
        db.session.commit()

        msg = f"Updated ticket '{ticket.key}' with the attributes: '{kwargs}'."
        current_app.logger.info(msg)

    @classmethod
    def delete(cls, ticket_id):
        ticket = cls.get(ticket_id=ticket_id)
        if ticket:
            db.session.delete(ticket)
            db.session.commit()

            current_app.logger.info(f"Deleted ticket '{ticket.key}'.")

    @classmethod
    def create_comment(
        cls,
        issue: typing.Union[Ticket, str],
        author: str,
        body: str,
        watchers: list = None,
        attachments: list = None,
    ):
        """Create the body of the ticket.

        :param issue: the ticket to comment on
        :param author: the author of the comment
        :param body: the body of the comment
        :param watchers: user emails to watch for ticket changes
        :param attachments: the files to attach to the comment which
                            are stored in Jira
        """
        svc = JiraSvc()

        # translate watchers into jira.User objects iff exists
        watchers = [cls.resolve_email(email, default=email) for email in watchers or []]

        body = cls.create_message_body(
            template="jira.j2",
            values={
                "author": svc.markdown.mention(user=author),
                "cc": " ".join(
                    svc.markdown.mention(user=watcher) for watcher in watchers
                ),
                "body": body,
            },
        )
        svc.add_comment(issue=issue, body=body, is_internal=True)

        # add watchers
        svc.add_watchers(issue=issue, watchers=watchers)

        # adding attachments
        for attachment in attachments or []:
            svc.add_attachment(issue=issue, attachment=attachment)

    @staticmethod
    def create_message_body(template=None, values=None) -> typing.Optional[str]:
        """Create the body of the ticket.

        :param template: the template to build ticket body from
        :param values: values for template interpolation
        """
        if not template:
            return None

        template_path = os.path.join(
            current_app.root_path, "templates", "ticket", "format"
        )
        template_filepath = os.path.join(template_path, template)
        if not os.path.exists(template_filepath):
            raise ValueError("Invalid template provided")

        with open(template_filepath) as file:
            content = file.read()

        return jinja2.Template(content).render(**values)

    @staticmethod
    def resolve_email(email, default=None) -> jira.resources.User:
        """Email translation to Jira user."""
        return next(iter(JiraSvc().search_users(query=email, maxResults=1)), default)
