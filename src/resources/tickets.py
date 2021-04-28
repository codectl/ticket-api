import flasgger
import marshmallow
from flask import current_app, request
from flask_restful import abort, Resource

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
            'boards': params.poplist('boards') or [current_app.config['JIRA_DEFAULT_BOARD']['key']],
            'categories': params.poplist('categories') or [current_app.config['JIRA_TICKET_LABEL_DEFAULT_CATEGORY']],
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
