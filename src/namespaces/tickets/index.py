from flask import request
from flask_restplus import Namespace, Resource

from src.dto.ticket import ro_fields, rw_fields
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
    @tickets.param('sort', description='sort tickets by', default='created', enum=['created'])
    @tickets.marshal_list_with(ro_fields)
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

    # @tickets.param('internal', description='if set to true, tag Jira ticket as internal', default=True)
    @tickets.response(201, 'Created')
    @tickets.expect(rw_fields, validate=True)
    @tickets.marshal_with(ro_fields, code=201)
    def post(self):
        """
        Create a new ticket.
        """
        TicketService.create(**request.get_json())
        return None, 201


@tickets.param('key', description='the ticket identifier')
@tickets.route('/<key>')
class Ticket(Resource):

    @tickets.response(200, 'Success')
    @tickets.response(404, 'Not found')
    @tickets.marshal_with(ro_fields)
    def get(self, key):
        """
        Get a ticket given its identifier
        """
        ticket = next(iter(TicketService.find_by(key=key, limit=1)), None)
        if not ticket:
            tickets.abort(404)
        else:
            return ticket
