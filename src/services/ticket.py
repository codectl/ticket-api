from typing import List, Optional, Union

from flask import current_app

from src import db
from src.models.Ticket import Ticket


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

    @staticmethod
    def find_by(fetch_one=False, **filters) -> Union[List[Ticket], Optional[Ticket]]:
        query = Ticket.query.filter_by(**filters)
        return query.all() if not fetch_one else query.one_or_none()

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
