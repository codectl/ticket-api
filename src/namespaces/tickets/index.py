from flask import request
from flask_restplus import Namespace, Resource

from src.dto.ticket import ticket as ticket_fields
from src.services.ticket import TicketService

tickets = Namespace(
    'tickets',
    description='Manage tickets.'
)


@tickets.route('/')
class Tickets(Resource):

    @tickets.param('limit', description='results limit', default=20)
    @tickets.param('boards', description='boards to fetch tickets from', enum=['support', 'sprint'])
    @tickets.param('q', description='searching for text occurrences')
    @tickets.param('reporter', description='the ticket reporter email')
    @tickets.param('assignee', description='the person email whose ticket is assigned to')
    @tickets.param('status', description='the ticket status')
    @tickets.param('watcher', description='tickets user has subscribed to')
    @tickets.param('sort', description='sort tickets by', default='created')
    @tickets.marshal_list_with(ticket_fields)
    @tickets.response(200, 'Success')
    @tickets.response(400, 'Bad request')
    def get(self):
        """
        Get service tickets based on search criteria.
        """
        params = request.args.copy()
        limit = params.pop('limit', 20)

        if not TicketService.validate_search_filters(**params):
            tickets.abort(400, 'Invalid search parameters')

        return TicketService.find_by(limit=limit, **params)


@tickets.route('/<key>')
class Ticket(Resource):

    @tickets.param('key', 'The ticket identifier')
    @tickets.response(200, 'Success')
    @tickets.response(404, 'Not found')
    @tickets.marshal_with(ticket_fields)
    def get(self, key):
        """
        Get a ticket given its identifier
        """
        ticket = next(TicketService.find_by(key=key, limit=1), None)
        if not ticket:
            tickets.abort(404)
        else:
            return ticket
