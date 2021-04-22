from flask import current_app, request
from flask_restful import Resource
from flasgger import swag_from

from src import swagger
from src.schemas.jira.issue import Issue
# from src.dto.ticket import ticket
from src.services.ticket import TicketService
from src.services.jira import JiraService


class Tickets(Resource):

    # @tickets.param('limit', description='results limit', default=20, required=True)
    # @tickets.param('boards', description='boards to fetch tickets from',
    #                type='array',
    #                items={'type': 'string', 'enum': JiraService.supported_board_keys()},
    #                default=[current_app.config['JIRA_DEFAULT_BOARD']['key']],
    #                required=True)
    # @tickets.param('category', description='category that the ticket belongs to',
    #                enum=JiraService.supported_categories(),
    #                default=current_app.config['JIRA_TICKET_LABEL_DEFAULT_CATEGORY'],
    #                required=True)
    # @tickets.param('q', description='searching for text occurrences')
    # @tickets.param('reporter', description='the ticket reporter email')
    # @tickets.param('assignee', description='the person email whose ticket is assigned to')
    # @tickets.param('status', description='the ticket status')
    # @tickets.param('watcher', description='tickets user has subscribed to')
    # @tickets.param('fields', description='additional fields to include in the results',
    #                type='array',
    #                items={'type': 'string', 'enum': JiraService.supported_fields()})
    # @tickets.param('sort', description='sort tickets by', default='created', enum=['created'])
    # @tickets.marshal_list_with(issue, skip_none=True)
    # @tickets.response(200, 'Ok')
    # @tickets.response(400, 'Bad request')
    @swag_from({
        'parameters': [
            {
                'in': 'query',
                'name': 'boards',
                'description': 'boards to fetch tickets from',
                'schema': {
                    'type': 'array',
                    'items': {
                        'type': 'string',
                        'enum': JiraService.supported_board_keys()
                    },
                },
                'default': [current_app.config['JIRA_DEFAULT_BOARD']['key']],
                'explode': False,
                'required': True
            }, {
                'in': 'query',
                'name': 'categories',
                'description': 'categories that the ticket belongs to',
                'schema': {
                    'type': 'array',
                    'items': {
                        'type': 'string',
                        'enum': JiraService.supported_categories()
                    },
                },
                'default': [current_app.config['JIRA_TICKET_LABEL_DEFAULT_CATEGORY']],
                'explode': False,
                'required': True
            }, {
                'in': 'query',
                'name': 'reporter',
                'description': 'ticket reporter email',
            }, {
                'in': 'query',
                'name': 'assignee',
                'description': 'user email whose ticket is assigned to',
            }, {
                'in': 'query',
                'name': 'status',
                'description': 'name of the current ticket status'
            }, {
                'in': 'query',
                'name': 'watcher',
                'description': 'tickets user has subscribed to',
            }, {
                'in': 'query',
                'name': 'q',
                'description': 'search for text occurrences',
            }, {
                'in': 'query',
                'name': 'fields',
                'description': 'additional fields to include in the results',
                'schema': {
                    'type': 'array',
                    'items': {
                        'type': 'string',
                        'enum': JiraService.supported_fields()
                    },
                }
            }, {
                'in': 'query',
                'name': 'limit',
                'description': 'results limit',
                'default': 20,
                'required': True
            }, {
                'in': 'query',
                'name': 'sort',
                'description': 'sort tickets by',
                'schema': {
                    'type': 'string',
                    'enum': ['created']
                },
                'default': 'created',
            }
        ],
        'responses': {
            200: {
                'description': 'Ok',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'array',
                            'items': {
                                '$ref': '#/components/schemas/Issue'
                            }
                        }
                    },
                }
            },
            400: {
                'description': 'Ok',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'string',
                            'example': 'ping'
                        }
                    }
                }
            }
        }
    })
    def get(self):
        """
        Get service tickets based on search criteria.
        """
        params = request.args.to_dict()
        limit = params.pop('limit', 20)
        boards = params.pop('boards', '').split(',')
        fields = params.pop('fields', '').split(',')

        return TicketService.find_by(limit=limit, boards=boards, fields=fields, **params)

    # @tickets.param('internal', description='if set to true, tag Jira ticket as internal', default=True)
    # parser = tickets.parser()
    # parser.add_argument('test', type=int, default=10, location='form')
    # parser.add_argument('ticket', location='body')
    #
    # @tickets.response(201, 'Created')
    # @tickets.response(400, 'Bad request')
    # # @tickets.expect(ticket)
    # @tickets.expect(parser)
    # # @tickets.param('attachments', description='files to attach',
    # #                type='file',
    # #                _in='formData')
    # # @tickets.marshal_with(issue, code=201)
    # def post(self):
    #     """
    #     Create a new ticket.
    #     """
    #     print(request.mimetype)
    #     print(tickets)
    #     print('--')
    #
    #     # try:
    #     #     return TicketService.create(
    #     #         attachments=request.form.get('attachments')
    #     #     ), 201
    #     # except jira.exceptions.JIRAError as ex:
    #     #     tickets.abort(400, ex.text)

# @tickets.param('key', description='the ticket identifier')
# @tickets.route('/<key>')
# class Ticket(Resource):
#
#     @tickets.response(200, 'Ok')
#     @tickets.response(404, 'Not found')
#     @tickets.marshal_with(issue, skip_none=True)
#     def get(self, key):
#         """
#         Get a ticket given its identifier
#         """
#         result = next(iter(TicketService.find_by(key=key, limit=1)), None)
#         if not result:
#             tickets.abort(404, 'Ticket not found')
#         else:
#             return ticket
