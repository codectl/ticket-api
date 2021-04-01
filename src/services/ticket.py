from typing import List, Optional, Union

from flask import current_app

from src import db
from src.models.Ticket import Ticket
from src.services.jira import JiraService


class TicketService:

    @classmethod
    def create(cls, **kwargs) -> Ticket:
        ticket = Ticket(**kwargs)

        db.session.add(ticket)
        db.session.commit()

        current_app.logger.info("Created ticket '{0}'.".format(ticket.jira_ticket_key))

        return ticket

    @staticmethod
    def get(ticket_id) -> Optional[Ticket]:
        return Ticket.query.get(ticket_id)

    @classmethod
    def find_one(cls, **filters) -> Optional[Ticket]:
        """
        Search for a single ticket based on several criteria.
        """

        return next(cls.find_by(limit=1, **filters))

    @classmethod
    def find_by(cls, limit=20, jira=True, **filters) -> Union[List[Ticket], Optional[Ticket]]:
        """
        Search for tickets based on several criteria.
        Jira filters are also supported.
        :param limit: the max number of results retrieved
        :param jira: whether to query Jira api to get results from
        """

        if jira:
            # fetch ticket from Jira
            jira = JiraService()
            query = jira.create_jql_query(**filters)
            jira_tickets = jira.search_issues(jql_str=query, maxResults=limit)

            tickets = []
            for jira_ticket in jira_tickets:
                ticket = cls.find_one(jira_ticket_key=jira_ticket.key, jira=False)
                ticket.jira = jira_ticket.raw
            return tickets
        else:
            return Ticket.query.filter_by(**filters)

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

            current_app.logger.info("Deleted ticket_id '{0}'.".format(ticket_id.jira_ticket_key))
