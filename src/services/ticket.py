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

        return next(iter(cls.find_by(limit=1, **filters)), None)

    @classmethod
    def find_by(cls, limit=20, jira=True, **filters) -> Union[List[Ticket], Optional[Ticket]]:
        """
        Search for tickets based on several criteria.
        Jira filters are also supported.

        :param limit: the max number of results retrieved
        :param jira: whether to query Jira api to get results from
        """

        # filter validation
        cls._validate_filters(**filters)

        # the Jira service instance
        jira_service = JiraService()

        if jira:

            # If any of the filter is not a Jira filter, then
            # apply local filter and pass on results to jql
            if any(not cls.is_jira_filter(filter_) for filter_ in filters):
                tickets = Ticket.query.filter_by(**filters).all()
                filters['key'] = filters.get('key', [ticket.jira_ticket_key for ticket in tickets])

            # fetch tickets from Jira using jql while skipping jql
            # validation since local db might not be synched with Jira
            query = jira_service.create_jql_query(**{k: v for k, v in filters.items() if cls.is_jira_filter(k)})
            jira_tickets = jira_service.search_issues(jql_str=query, maxResults=limit, validate_query=False)

            tickets = []
            for jira_ticket in jira_tickets:
                ticket = cls.find_one(jira_ticket_key=jira_ticket.key, jira=False)
                # prevent cases where local db is not synched with Jira
                # for cases where Jira tickets are not yet locally present
                if ticket:
                    ticket.jira = jira_ticket.raw
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

    @classmethod
    def remove_deleted(cls, tickets):
        """
        Remove tickets deleted from Jira.
        """
        jira_service = JiraService()
        result = []
        for ticket in tickets:
            if not jira_service.exists_issue(issue_id=ticket.jira_ticket_key):
                cls.delete(ticket.id)
            else:
                result.append(ticket)
        return result

    @staticmethod
    def _validate_filters(**filters):
        """
        Validate query filters.

        The following fields are managed locally, therefore they
        have no relationship with Jira ticket data. Such fields
        cannot be used in combination with other fields.
        - reporter: represents the owner of the ticket.
        """

        invalid_combinations_fields = {
            'reporter': ['limit', 'q', 'key', 'assignee', 'status', 'watcher']
        }
        matches = [field for field, values in invalid_combinations_fields.items() if
                   field in filters and any(f in values for f in filters)]
        if matches:
            raise ValueError(' '.join(("Field {0} cannot be used in combination with fields {1}."
                                      .format(match, invalid_combinations_fields[match]) for match in matches)))
        return True

    @staticmethod
    def is_jira_filter(filter_):
        """
        Check whether given filter is a Jira only filter.
        """

        return filter_ in ['boards', 'q', 'key', 'assignee', 'status', 'watcher', 'sort']

