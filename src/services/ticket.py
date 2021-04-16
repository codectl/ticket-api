import os
from typing import List, Optional, Union

import jinja2
import jira
import requests
from flask import current_app

from src import db
from src.models.Ticket import Ticket
from src.models.jira.Board import Board
from src.services.jira import JiraService


class TicketService:

    @classmethod
    def create(cls, **kwargs) -> Ticket:

        jira_service = JiraService()

        # translate reporter into a Jira account
        reporter = next(iter(jira_service.search_users(user=kwargs.get('reporter'), limit=1)), None)

        # create ticket body with Jira markdown format
        body = cls.create_ticket_body(
            author=jira_service.markdown.mention(reporter=reporter or kwargs.get('reporter')),
            body=kwargs.get('description')
        )

        # if reporter is not a Jira account, reporter is set to 'Anonymous'
        reporter_id = getattr(reporter, 'accountId', None)

        # set defaults
        board_key = kwargs.get('board', Board.default().key)
        project_key = jira_service.find_board(key=board_key).project['projectKey']
        priority = dict(name=kwargs.get('priority').capitalize() if kwargs.get('priority') else 'None')

        category = kwargs.pop('category', current_app.config['JIRA_TICKET_LABEL_DEFAULT_CATEGORY'])
        categories = category.split(',') + current_app.config['JIRA_TICKET_LABELS']

        # create ticket in Jira
        issue = jira_service.create_issue(summary=kwargs.get('title'),
                                          description=body,
                                          reporter=dict(id=reporter_id),
                                          project=dict(key=project_key),
                                          issuetype=dict(name=current_app.config['JIRA_TICKET_TYPE']),
                                          labels=categories,
                                          priority=priority)

        print(issue)

        # add watchers iff has permission
        if kwargs.get('watchers') and jira_service.has_permissions(permissions=['MANAGE_WATCHERS'],
                                                                   issue_key=issue.key):
            # check whether watcher has permissions to watch the issue
            for email in kwargs.get('watchers'):
                user = next(iter(jira_service.search_users(user=email, limit=1)), None)
                if user is not None:
                    # check whether watcher has permissions to watch the issue
                    try:
                        jira_service.add_watcher(issue=issue.key,
                                                 watcher=user.accountId)
                    except jira.exceptions.JIRAError as e:
                        if e.status_code == requests.codes.unauthorized:
                            current_app.logger.warning("Watcher '{0}' has no permission to watch issue '{1}'."
                                                       .format(user.displayName, issue.key))
                        else:
                            raise e

        # add new entry to the db
        local_fields = {k: v for k, v in kwargs.items() if k in Ticket.__dict__}
        ticket = Ticket(key=issue.key, **local_fields)

        db.session.add(ticket)
        db.session.commit()

        current_app.logger.info("Created ticket '{0}'.".format(ticket.key))

        return TicketService.find_by(key=ticket.key, limit=1)

    @staticmethod
    def get(ticket_id) -> Optional[Ticket]:
        return Ticket.query.get(ticket_id)

    @classmethod
    def find_one(cls, **filters) -> Optional[Ticket]:
        """
        Search for a single ticket based on several criteria.
        """
        return next(iter(cls.find_by(limit=1, **filters)), None)

    @classmethod
    def find_by(cls, limit=20, expand='jira', **filters) -> Union[List[Ticket], Optional[Ticket]]:
        """
        Search for tickets based on several criteria.
        Jira filters are also supported.

        :param limit: the max number of results retrieved
        :param expand: fields to include together with results. values: 'jira'
        :param filters: the query filters
        """
        jira_service = JiraService()

        # split filters
        local_filters = {k: v for k, v in filters.items() if k in Ticket.__dict__}
        jira_filters = {k: v for k, v in filters.items() if cls.is_jira_filter(k)}

        if expand and 'jira' in expand.split(','):

            # if any of the filter is not a Jira filter, then
            # apply local filter and pass on results to jql
            if local_filters:
                tickets = Ticket.query.filter_by(**local_filters).all()
                jira_filters['key'] = [ticket.key for ticket in tickets]

            # set Jira default values
            category = filters.pop('category', current_app.config['JIRA_TICKET_LABEL_DEFAULT_CATEGORY'])
            categories = category.split(',') + current_app.config['JIRA_TICKET_LABELS']

            # fetch tickets from Jira using jql while skipping jql
            # validation since local db might not be synched with Jira
            query = jira_service.create_jql_query(
                labels=categories,
                summary=filters.pop('q', None),
                **jira_filters
            )

            # include additional fields together with ticket
            fields = '*all, watcher, comments, attachments'

            issues = jira_service.search_issues(
                jql_str=query,
                maxResults=limit,
                validate_query=False,
                fields=fields
            )

            tickets = []
            for issue in issues:
                import pprint
                pprint.pprint(vars(issue))
                ticket = cls.find_one(key=issue.key, expand=None)
                # prevent cases where local db is not synched with Jira
                # for cases where Jira tickets are not yet locally present
                if ticket:
                    ticket.jira = issue
                    ticket.jira.url = "{0}/browse/{1}".format(current_app.config['ATLASSIAN_URL'], issue.key),
                    tickets.append(ticket)
            return tickets
        else:
            return Ticket.query.filter_by(**local_filters).all()

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

    @staticmethod
    def is_jira_filter(filter_):
        """
        Check whether given filter is a Jira only filter.
        """

        return filter_ in ['assignee', 'boards', 'category', 'key', 'q', 'sort', 'status', 'watcher']

    @staticmethod
    def create_ticket_body(template='default.j2', **kwargs):
        """
        Create the body of the ticket.

        :param template: the template to build ticket body from
        :param kwargs: values for template interpolation
        """
        if not template:
            return None

        template_path = os.path.join(current_app.root_path, 'templates', 'ticket', 'format')
        template_filepath = os.path.join(template_path, template)
        if not os.path.exists(template_filepath):
            raise ValueError('Invalid template provided')

        with open(template_filepath) as file:
            content = file.read()

        return jinja2.Template(content).render(**kwargs)
