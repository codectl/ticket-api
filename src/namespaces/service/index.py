from flask import request
from flask_restplus import Namespace, Resource

from src.models.Ticket import TicketDTO
from src.services.ticket import TicketService

service = Namespace(
    'service',
    description='Manage service tickets.'
)

ticket_fields = TicketDTO.ticket
ticket_mask = 'jira_key,jira_url'


@service.route('/')
class ServiceTickets(Resource):

    @service.param('limit', description='results limit. default: 20')
    @service.param('boards', description='boards to fetch tickets from', enum=['support', 'sprint'])
    @service.param('q', description='searching for text occurrences')
    @service.param('key', description='Jira ticket key')
    @service.param('reporter', description='the ticket reporter email')
    @service.param('assignee', description='the person email whose ticket is assigned to')
    @service.param('status', description='the ticket status')
    @service.param('watcher', description='tickets user has subscribed to')
    @service.param('sort', description='order to sort tickets by. default: created')
    @service.marshal_list_with(ticket_fields)
    @service.response(200, 'Success')
    def get(self):
        """
        Get service tickets based on search criteria.
        """
        params = request.args.copy()
        limit = params.pop('limit', 20)

        return TicketService.find_by(limit=limit, **params)


@service.route('/<key>')
class ServiceTicket(Resource):

    @service.param('key', 'The ticket identifier')
    @service.response(200, 'Success')
    @service.response(404, 'Not found')
    @service.marshal_with(ticket_fields)
    def get(self, key):
        """
        Get a ticket given its identifier
        """

        ticket = TicketService.find_by(jira_ticket_key=key, fetch_one=True)
        if not ticket:
            service.abort(404)
        else:
            return ticket
