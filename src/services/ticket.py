import os
from typing import List, Optional, Union

import jinja2
from flask import current_app

from src import db
from src.models.Ticket import Ticket
from src.services.jira import JiraService


class TicketService:

    @classmethod
    def create(
            cls,
            attachments: list = None,
            **kwargs
    ) -> dict:
        """
        Create a new ticket by calling Jira API to create a new
        issue. A new local reference is also created.

        :param attachments: the files to attach to the ticket which
                            are stored in Jira
        :param kwargs: properties of the ticket
            title: title of the ticket
            description: body of the ticket
            reporter: email of the author's ticket
            board: which board the ticket belongs to
            category: which category to assign ticket to
            priority: severity of the ticket
            watchers: user emails to watch for ticket changes
        """
        jira_service = JiraService()

        # translate emails into jira.User objects
        reporter = cls._email_to_user(kwargs.get('reporter'))
        watchers = [cls._email_to_user(email, default=email) for email in kwargs.get('watchers') or []]

        # create ticket body with Jira markdown format
        body = cls.create_ticket_body(
            template='jira.j2',
            values={
                'author': jira_service.markdown.mention(user=reporter or kwargs.get('reporter')),
                'cc': ' '.join(jira_service.markdown.mention(user=watcher) for watcher in watchers),
                'body': kwargs.get('body')
            }
        )

        # if reporter is not a Jira account, reporter is set to 'Anonymous'
        reporter_id = getattr(reporter, 'accountId', None)

        # set defaults
        board_key = kwargs.get('board')
        project_key = jira_service.find_board(key=board_key).project['projectKey']
        priority = (kwargs.get('priority') or '').lower()
        priority = priority if priority in ['high', 'low'] else 'None'
        priority = dict(name=priority.capitalize())

        category = kwargs.pop('category')
        categories = category.split(',') + current_app.config['JIRA_TICKET_LABELS']

        # create ticket in Jira
        issue = jira_service.create_issue(
            summary=kwargs.get('title'),
            description=body,
            reporter=dict(id=reporter_id),
            project=dict(key=project_key),
            issuetype=dict(name=current_app.config['JIRA_TICKET_TYPE']),
            labels=categories,
            priority=priority
        )

        # add watchers
        jira_service.add_watchers(
            key=issue.key,
            watchers=watchers
        )

        # adding attachments
        for attachment in attachments or []:
            jira_service.add_attachment(issue=issue, attachment=attachment)

        # add new entry to the db
        local_fields = {k: v for k, v in kwargs.items() if k in Ticket.__dict__}
        ticket = Ticket(key=issue.key, **local_fields)

        db.session.add(ticket)
        db.session.commit()

        current_app.logger.info("Created ticket '{0}'.".format(ticket.key))

        return TicketService.find_one(key=ticket.key)

    @staticmethod
    def get(ticket_id) -> Optional[Ticket]:
        return Ticket.query.get(ticket_id)

    @classmethod
    def find_one(cls, **filters) -> Optional[Union[dict, Ticket]]:
        """
        Search for a single ticket based on several criteria.
        """
        return next(iter(cls.find_by(limit=1, **filters)), None)

    @classmethod
    def find_by(
            cls,
            limit: int = 20,
            fields: list = None,
            _model: bool = False,
            **filters
    ) -> Union[List[dict], List[Ticket]]:
        """
        Search for tickets based on several criteria.
        Jira filters are also supported.

        :param limit: the max number of results retrieved
        :param fields: additional fields to include in results schema
        :param _model: whether to return a ticket model or cross results Jira data
        :param filters: the query filters
        """

        # split filters
        local_filters = {k: v for k, v in filters.items() if k in Ticket.__dict__}
        jira_filters = {k: v for k, v in filters.items() if JiraService.is_jira_filter(k)}

        if _model:
            return Ticket.query.filter_by(**local_filters).all()
        else:
            jira_service = JiraService()

            # if any of the filter is not a Jira filter, then
            # apply local filter and pass on results to jql
            if local_filters:
                tickets = Ticket.query.filter_by(**local_filters).all()

                # skip routine if no local entries are found
                if not tickets:
                    return []
                jira_filters['key'] = [ticket.key for ticket in tickets]

            # fetch tickets from Jira using jql while skipping jql
            # validation since local db might not be synched with Jira
            query = jira_service.create_jql_query(
                summary=filters.pop('q', None),
                labels=current_app.config['JIRA_TICKET_LABELS'],
                tags=filters.pop('categories', []),
                **jira_filters
            )

            # include additional fields
            fields = fields or []
            if '*navigable' not in fields:
                fields.append('*navigable')
            rendered = 'renderedFields' if 'rendered' in fields else 'fields'

            # remove plurals in fields
            issues = jira_service.search_issues(
                jql_str=query,
                maxResults=limit,
                validate_query=False,
                fields=','.join([field[:-1] if field.endswith('s') else field for field in fields]),
                expand=rendered
            )

            tickets = []
            for issue in issues:
                model = cls.find_one(key=issue.key, _model=True)

                # prevent cases where local db is not synched with Jira
                # for cases where Jira tickets are not yet locally present
                if model:
                    ticket = issue.raw['fields']
                    ticket['id'] = issue.id
                    ticket['key'] = issue.key
                    ticket['url'] = "{0}/browse/{1}".format(current_app.config['ATLASSIAN_URL'], issue.key)
                    ticket['reporter'] = {
                        'emailAddress': model.reporter
                    }

                    # add rendered fields if requested
                    if 'rendered' in fields:
                        ticket['rendered'] = issue.raw['renderedFields']

                    # add watchers if requested
                    if 'watchers' in fields:
                        ticket['watchers'] = jira_service.watchers(issue.key).raw['watchers']

                    tickets.append(ticket)
            return tickets

    @classmethod
    def update(cls, ticket_id, **kwargs):
        ticket = cls.get(ticket_id=ticket_id)
        for key, value in kwargs.items():
            if hasattr(ticket, key):
                setattr(ticket, key, value)
        db.session.commit()

        current_app.logger.info("Updated ticket_id '{0}' with the following attributes: '{1}'."
                                .format(ticket_id.key, kwargs))

    @classmethod
    def delete(cls, ticket_id):
        ticket = cls.get(ticket_id=ticket_id)
        if ticket:
            db.session.delete(ticket)
            db.session.commit()

            current_app.logger.info("Deleted ticket '{0}'.".format(ticket.key))

    @classmethod
    def create_comment(
            cls,
            key: str,
            author: str,
            body: str,
            watchers: list = None,
            attachments: list = None,
    ):
        """
        Create the body of the ticket.

        :param key: the ticket key to comment on
        :param author: the author of the comment
        :param body: the body of the comment
        :param watchers: user emails to watch for ticket changes
        :param attachments: the files to attach to the comment which
                            are stored in Jira
        """
        jira_service = JiraService()

        # translate watchers into jira.User objects iff exists
        watchers = [cls._email_to_user(email, default=email) for email in watchers or []]

        body = cls.create_ticket_body(
            template='jira.j2',
            values={
                'author': jira_service.markdown.mention(user=author),
                'cc': ' '.join(jira_service.markdown.mention(user=watcher) for watcher in watchers),
                'body': body
            }
        )
        jira_service.add_comment(issue=key, body=body, is_internal=True)

        # add watchers
        jira_service.add_watchers(key=key, watchers=watchers)

        # adding attachments
        for attachment in attachments or []:
            jira_service.add_attachment(issue=key, attachment=attachment)

    @staticmethod
    def create_ticket_body(template=None, values=None):
        """
        Create the body of the ticket.

        :param template: the template to build ticket body from
        :param values: values for template interpolation
        """
        if not template:
            return None

        template_path = os.path.join(current_app.root_path, 'templates', 'ticket', 'format')
        template_filepath = os.path.join(template_path, template)
        if not os.path.exists(template_filepath):
            raise ValueError('Invalid template provided')

        with open(template_filepath) as file:
            content = file.read()

        return jinja2.Template(content).render(**values)

    @staticmethod
    def _email_to_user(email, default=None):
        """ Email translation to Jira user """
        jira_service = JiraService()
        return next(iter(jira_service.search_users(user=email, limit=1)), default)
