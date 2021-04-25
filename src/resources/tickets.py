import flasgger
from flask import abort, current_app, request
from flask_restful import Resource

from src.serializers.inbound.tickets import TicketSearchCriteria
from src.serializers.outbound.jira.issue import IssueSchema
from src.services.ticket import TicketService
from src.services.jira import JiraService


class Tickets(Resource):

    @flasgger.swag_from({
        'parameters': flasgger.marshmallow_apispec.schema2parameters(
            TicketSearchCriteria,
            location='query'
        ),
        # 'parameters': [
        #     {
        #         'in': 'query',
        #         'name': 'boards',
        #         'description': 'boards to fetch tickets from',
        #         'schema': {
        #             'type': 'array',
        #             'items': {
        #                 'type': 'string',
        #                 'enum': JiraService.supported_board_keys()
        #             },
        #         },
        #         'default': [current_app.config['JIRA_DEFAULT_BOARD']['key']],
        #         'explode': False
        #     }, {
        #         'in': 'query',
        #         'name': 'categories',
        #         'description': 'categories that the ticket belongs to',
        #         'schema': {
        #             'type': 'array',
        #             'items': {
        #                 'type': 'string',
        #                 'enum': JiraService.supported_categories()
        #             },
        #         },
        #         'default': [current_app.config['JIRA_TICKET_LABEL_DEFAULT_CATEGORY']],
        #         'explode': False
        #     }, {
        #         'in': 'query',
        #         'name': 'reporter',
        #         'description': 'ticket reporter email',
        #     }, {
        #         'in': 'query',
        #         'name': 'assignee',
        #         'description': 'user email whose ticket is assigned to',
        #     }, {
        #         'in': 'query',
        #         'name': 'status',
        #         'description': 'name of the current ticket status'
        #     }, {
        #         'in': 'query',
        #         'name': 'watcher',
        #         'description': 'tickets user has subscribed to',
        #     }, {
        #         'in': 'query',
        #         'name': 'q',
        #         'description': 'search for text occurrences',
        #     }, {
        #         'in': 'query',
        #         'name': 'fields',
        #         'description': 'additional fields to include in the results',
        #         'schema': {
        #             'type': 'array',
        #             'items': {
        #                 'type': 'string',
        #                 'enum': JiraService.supported_fields()
        #             },
        #         }
        #     }, {
        #         'in': 'query',
        #         'name': 'limit',
        #         'description': 'results limit',
        #         'default': 20
        #     }, {
        #         'in': 'query',
        #         'name': 'sort',
        #         'description': 'sort tickets by',
        #         'schema': {
        #             'type': 'string',
        #             'enum': ['created']
        #         },
        #         'default': 'created',
        #     }
        # ],
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
            400: {'$ref': '#/components/responses/BadRequest'}
        }
    })
    def get(self):
        """
        Get service tickets based on search criteria.
        """
        # def validation():
        #     """
        #     Validate query parameters
        #     """
        #     if not all(board in JiraService.supported_board_keys() for board in params.get('boards', '').split(',')):
        #         raise Va

        from src import swagger
        from pprint import pprint
        pprint(swagger.get_apispecs('swagger'))
        params = request.args.to_dict()

        # consider default values
        tickets = TicketService.find_by(
            boards=params.pop('boards', current_app.config['JIRA_DEFAULT_BOARD']['key']).split(','),
            categories=params.pop('categories', current_app.config['JIRA_TICKET_LABEL_DEFAULT_CATEGORY']).split(','),
            fields=params.pop('fields', '').split(','),
            limit=params.pop('limit', 20),
            sort=params.pop('sort', 'created'),
            **params
        )

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

    @flasgger.swag_from({
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
            404: {'$ref': '#/components/responses/NotFound'}
        }
    })
    def get(self, key):
        """
        Get a ticket given its identifier
        """

        # search for ticket across supported boards and categories
        result = next(iter(TicketService.find_by(
            key=key,
            boards=JiraService.supported_board_keys(),
            categories=JiraService.supported_categories(),
            limit=1
        )), None)
        if not result:
            abort(404, 'Ticket not found')
        else:
            return IssueSchema().dump(result)
