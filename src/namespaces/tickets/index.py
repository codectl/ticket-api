import jira
from flask import current_app, request
from flask_restplus import Namespace, Resource

from src.dto.ticket import ro_fields, rw_fields
from src.services.ticket import TicketService
from src.services.jira import JiraService

tickets = Namespace(
    'tickets',
    description='Manage tickets.'
)


@tickets.route('/')
class Tickets(Resource):

    @tickets.param('limit', description='results limit', default=20, required=True)
    @tickets.param('boards', description='boards to fetch tickets from',
                   enum=JiraService.supported_board_keys(),
                   default=current_app.config['JIRA_DEFAULT_BOARD']['key'])
    @tickets.param('category', description='category that the ticket belongs to',
                   enum=JiraService.supported_categories(),
                   default=current_app.config['JIRA_TICKET_LABEL_DEFAULT_CATEGORY'],
                   required=True)
    @tickets.param('q', description='searching for text occurrences')
    @tickets.param('reporter', description='the ticket reporter email')
    @tickets.param('assignee', description='the person email whose ticket is assigned to')
    @tickets.param('status', description='the ticket status')
    @tickets.param('watcher', description='tickets user has subscribed to')
    @tickets.param('sort', description='sort tickets by', default='created', enum=['created'])
    @tickets.marshal_list_with(ro_fields)
    @tickets.response(200, 'Ok')
    @tickets.response(400, 'Bad request')
    def get(self):
        """
        Get service tickets based on search criteria.
        """
        params = request.args.copy()
        limit = params.pop('limit', 20)
        boards = params.pop('boards', '').split(',')

        return TicketService.find_by(limit=limit, boards=boards, **params)

    # @tickets.param('internal', description='if set to true, tag Jira ticket as internal', default=True)
    @tickets.response(201, 'Created')
    @tickets.response(400, 'Bad request')
    @tickets.expect(rw_fields, validate=True)
    @tickets.marshal_with(ro_fields, code=201)
    def post(self):
        """
        Create a new ticket.
        """
        try:
            return TicketService.create(**request.get_json()), 201
        except jira.exceptions.JIRAError as ex:
            tickets.abort(400, ex.text)


@tickets.param('key', description='the ticket identifier')
@tickets.route('/<key>')
class Ticket(Resource):

    @tickets.response(200, 'Ok')
    @tickets.response(404, 'Not found')
    @tickets.marshal_with(ro_fields, skip_none=True)
    def get(self, key):
        """
        Get a ticket given its identifier
        """
        ticket = next(iter(TicketService.find_by(key=key, limit=1)), None)
        if not ticket:
            tickets.abort(404, 'Ticket not found')
        else:
            return ticket
