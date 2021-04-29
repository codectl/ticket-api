import flasgger
import jira
import marshmallow
from flask import request
from flask_restful import abort, Resource

from src.serializers.inbound.CreateTicket import CreateTicketSchema
from src.serializers.inbound.TicketSearchCriteria import TicketSearchCriteriaSchema
from src.serializers.outbound.jira.Issue import IssueSchema
from src.services.ticket import TicketService
from src.services.jira import JiraService


class Tickets(Resource):

    @flasgger.swag_from({
        'parameters': flasgger.marshmallow_apispec.schema2parameters(
            TicketSearchCriteriaSchema,
            location='query'
        ),
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

        # read params and set defaults
        params = request.args.copy()
        filters = {
            'boards': params.poplist('boards') or JiraService.supported_board_keys(),
            'categories': params.poplist('categories') or JiraService.supported_categories(),
            'fields': params.poplist('fields'),
            'limit': params.get('limit', 20),
            'sort': params.get('sort', 'created'),
            **params
        }

        # validate parameters
        errors = TicketSearchCriteriaSchema().validate(filters)
        if errors:
            abort(400, status=400, message=errors)

        # consider default values
        tickets = TicketService.find_by(**filters)

        return IssueSchema(many=True).dump(tickets)

    @flasgger.swag_from({
        'requestBody': {
            'required': True,
            'content': {
                'application/json': {
                    'schema': CreateTicketSchema
                },
                'multipart/form-data': {
                    'schema': CreateTicketSchema
                }
            }
        },
        'responses': {
            201: {
                'description': 'Created',
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
            400: {'$ref': '#/components/responses/BadRequest'},
            415: {'$ref': '#/components/responses/UnsupportedMediaType'}
        }
    })
    def post(self):
        """
        Create a new ticket.
        """
        body = None
        errors = None
        if request.mimetype == 'application/json':
            body = request.json
            errors = CreateTicketSchema().validate(body)
        elif request.mimetype == 'multipart/form-data':
            pass
        else:
            abort(415, status=415, message='Unsupported media type')

        if errors:
            abort(400, status=400, message=errors)

        try:
            created = TicketService.create(**body)
            return IssueSchema().dump(created), 201
        except jira.exceptions.JIRAError as ex:
            abort(400, status=400, message=ex.text)


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


class Ticket(Resource):

    @flasgger.swag_from({
        'parameters': flasgger.marshmallow_apispec.schema2parameters(
            marshmallow.Schema.from_dict({
                'key': marshmallow.fields.String(
                    required=True,
                    metadata=dict(description='ticket unique identifier')
                )
            }),
            location='path'
        ),
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
            abort(404, status=404, message='Ticket not found')
        else:
            return IssueSchema().dump(result)
