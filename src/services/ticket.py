import os
from typing import List, Optional, Union

import jinja2
from flask import current_app

from src import db
from src.models.Ticket import Ticket
from src.services.jira import JiraService


class TicketService:

    @classmethod
    def create(cls, **kwargs) -> Ticket:

        # the Jira service instance
        jira_service = JiraService()

        # translate reporter into a Jira account
        reporter = next(iter(jira_service.search_users(user=kwargs.get('reporter'))), None)

        # create ticket body with Jira markdown format
        body = cls.create_ticket_body(
            author=jira_service.markdown.mention(reporter=reporter or kwargs.get('reporter')),
            body=kwargs.get('description')
        )

        # if reporter is not a Jira account,
        # reporter is set to 'Anonymous'
        reporter_id = getattr(reporter, 'accountId', None)

        # get board to find its project
        board = jira_service.find_board('support')

        issue = jira_service.create_issue(summary=kwargs.get('title'),
                                          description=body,
                                          reporter=dict(id=reporter_id),
                                          project=dict(key=project),
                                          issuetype=dict(name=current_app.config['JIRA_TICKET_TYPE']),
                                          labels=current_app.config['JIRA_TICKET_LABELS'],
                                          priority=dict(name=kwargs.get('priority')))
        print(issue)
        # ticket = Ticket(**kwargs)
        #
        # db.session.add(ticket)
        # db.session.commit()

        # current_app.logger.info("Created ticket '{0}'.".format(ticket.jira_ticket_key))
        #
        # return ticket
        return None

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
    def find_by(cls, limit=20, jira=True, **filters) -> Union[List[Ticket], Optional[Ticket]]:
        """
        Search for tickets based on several criteria.
        Jira filters are also supported.

        :param limit: the max number of results retrieved
        :param jira: whether to query Jira api to get results from
        :param filters: the query filters
        """

        # the Jira service instance
        jira_service = JiraService()

        # split filters
        local_filters = {k: v for k, v in filters.items() if not cls.is_jira_filter(k)}
        jira_filters = {k: v for k, v in filters.items() if cls.is_jira_filter(k)}

        if jira:

            # if any of the filter is not a Jira filter, then
            # apply local filter and pass on results to jql
            if local_filters:
                tickets = Ticket.query.filter_by(**local_filters).all()
                jira_filters['key'] = [ticket.jira_ticket_key for ticket in tickets]

            # fetch tickets from Jira using jql while skipping jql
            # validation since local db might not be synched with Jira
            query = jira_service.create_jql_query(**jira_filters)
            jira_tickets = jira_service.search_issues(jql_str=query, maxResults=limit, validate_query=False)

            tickets = []
            for jira_ticket in jira_tickets:
                ticket = cls.find_one(jira_ticket_key=jira_ticket.key, jira=False)
                # prevent cases where local db is not synched with Jira
                # for cases where Jira tickets are not yet locally present
                if ticket:
                    ticket.jira = jira_ticket
                    ticket.jira.url = ticket.jira_ticket_url
                    tickets.append(ticket)
            return tickets
        else:
            return Ticket.query.filter_by(**filters).all()

    @classmethod
    def update(cls, ticket_id, **kwargs):
        ticket = cls.get(ticket_id=ticket_id)
        for key, value in kwargs.items():
            if hasattr(ticket, key):
                setattr(ticket, key, value)
        db.session.commit()

        current_app.logger.info("Updated ticket_id '{0}' with the following attributes: '{1}'."
                                .format(ticket_id.jira_ticket_key, kwargs))

    @classmethod
    def delete(cls, ticket_id):
        ticket = cls.get(ticket_id=ticket_id)
        if ticket:
            db.session.delete(ticket)
            db.session.commit()

            current_app.logger.info("Deleted ticket '{0}'.".format(ticket.jira_ticket_key))

    @staticmethod
    def is_jira_filter(filter_):
        """
        Check whether given filter is a Jira only filter.
        """

        return filter_ in ['boards', 'q', 'key', 'assignee', 'status', 'watcher', 'sort']

    @staticmethod
    def validate_search_filters(**filters):
        """
        Validate query search filters.
        """

        # guarantee that board filter is part of supported boards
        if filters.get('board') and filters['board'] not in current_app.config['JIRA_BOARDS']:
            return False
        return True

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
