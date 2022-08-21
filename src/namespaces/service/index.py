from flask import request
from flask_restplus import marshal, Namespace, Resource

from src.dto.ticket import ticket as ticket_fields
from src.services.ticket import TicketService

service = Namespace(
    'service',
    description='Manage service tickets.'
)

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
    @service.response(400, 'Bad request')
    def get(self):
        """
        Get service tickets based on search criteria.
        """
        params = request.args.copy()
        limit = params.pop('limit', 20)

        if not TicketService.validate_search_filters(**params):
            service.abort(400, 'Invalid search parameters')

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
        ticket = next(TicketService.find_by(key=key, limit=1), None)
        if not ticket:
            service.abort(404)
        else:
            return ticket
