from flask import abort, current_app, request
from flask_restful import Resource
from flasgger import swag_from

from src.oas3.components.schemas.jira.issue import IssueSchema
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
                'description': 'Bad request'
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

        tickets = TicketService.find_by(limit=limit, boards=boards, fields=fields, **params)
        return IssueSchema(many=True).dump(tickets)

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
    # @swagger.validate('UserSchema')
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


class Ticket(Resource):

    @swag_from({
        'parameters': [
            {
                'in': 'path',
                'name': 'key',
                'description': 'ticket unique identifier',
            }
        ],
        'responses': {
            200: {
                'description': 'Ok',
                'content': {
                    'application/json': {
                        'schema': {
                            '$ref': '#/components/schemas/Issue'
                        }
                    },
                }
            },
            404: {
                'description': 'Not found',
                'content': {
                    'application/json': {
                    },
                }
            }
        }
    })
    def get(self, key):
        """
        Get a ticket given its identifier
        """
        result = next(iter(TicketService.find_by(key=key, limit=1)), None)
        print(key)
        if not result:
            abort(404, 'Ticket not found')
        else:
            return IssueSchema().dump(result)
