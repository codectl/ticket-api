import flasgger
import jira
import marshmallow
from flask import request, jsonify
from flask_restful import abort, Resource

from src import api
from src.serializers.inbound.CreateTicket import CreateTicketSchema
from src.serializers.inbound.CreateTicketComment import CreateTicketCommentSchema
from src.serializers.inbound.TicketSearchCriteria import TicketSearchCriteriaSchema
from src.serializers.outbound.jira.Issue import IssueSchema
from src.services.ticket import TicketService
from src.services.jira import JiraService


@api.resource('/tickets', endpoint='tickets')
class Tickets(Resource):

    @flasgger.swag_from({
        'parameters': flasgger.marshmallow_apispec.schema2parameters(
            TicketSearchCriteriaSchema,
            location='query'
        ),
        'tags': ['tickets'],
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
        },
    })
    def get(self):
        """
        Get service tickets based on search criteria
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
                    'schema': flasgger.marshmallow_apispec.schema2jsonschema(CreateTicketSchema)
                },
                'multipart/form-data': {
                    'schema': flasgger.marshmallow_apispec.schema2jsonschema(
                        marshmallow.Schema.from_dict({
                            **CreateTicketSchema().fields,
                            'attachments': marshmallow.fields.List(
                                marshmallow.fields.Raw(
                                    metadata=dict(
                                        type='file',
                                        description='files to attach'
                                    )
                                )
                            )
                        })
                    )
                }
            }
        },
        'tags': ['tickets'],
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
                    }
                }
            },
            400: {'$ref': '#/components/responses/BadRequest'},
            415: {'$ref': '#/components/responses/UnsupportedMediaType'}
        }
    })
    def post(self):
        """
        Create a new ticket
        """
        body = {}
        files = []
        if request.mimetype == 'application/json':
            body = request.json
        elif request.mimetype == 'multipart/form-data':
            body = request.form.to_dict(flat=True)
            files = request.files.to_dict(flat=False).get('attachments', [])
        else:
            abort(415, status=415, message='Unsupported media type')

        # validate body
        errors = CreateTicketSchema().validate(body)
        if errors:
            abort(400, status=400, message=errors)

        try:
            created = TicketService.create(**body, attachments=files)
            return IssueSchema().dump(created), 201
        except jira.exceptions.JIRAError as ex:
            abort(400, status=400, message=ex.text)


@api.resource('/tickets/<key>', endpoint='ticket')
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
        'tags': ['tickets'],
        'responses': {
            200: {
                'description': 'Ok',
                'content': {
                    'application/json': {
                        'schema': {
                            '$ref': '#/components/schemas/Issue'
                        }
                    }
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


@api.resource('/tickets/<key>/comment', endpoint='comment')
class Comment(Resource):

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
        'tags': ['tickets'],
        'requestBody': {
            'required': True,
            'content': {
                'application/json': {
                    'schema': flasgger.marshmallow_apispec.schema2jsonschema(CreateTicketCommentSchema)
                },
                'multipart/form-data': {
                    'schema': flasgger.marshmallow_apispec.schema2jsonschema(
                        marshmallow.Schema.from_dict({
                            **CreateTicketCommentSchema().fields,
                            'attachments': marshmallow.fields.List(
                                marshmallow.fields.Raw(
                                    metadata=dict(
                                        type='file',
                                        description='files to attach'
                                    )
                                )
                            )
                        })
                    )
                }
            }
        },
        'responses': {
            201: {
                'description': 'Created',
                'content': {
                    'application/json': {
                        'schema': {
                            '$ref': '#/components/schemas/Issue'
                        }
                    }
                }
            },
            400: {'$ref': '#/components/responses/BadRequest'},
            415: {'$ref': '#/components/responses/UnsupportedMediaType'}
        }
    })
    def post(self, key):
        """
        Create a new ticket comment
        """
        body = {}
        files = []
        if request.mimetype == 'application/json':
            body = request.json
        elif request.mimetype == 'multipart/form-data':
            body = request.form.to_dict(flat=True)
            files = request.files.to_dict(flat=False).get('attachments', [])
        else:
            abort(415, status=415, message='Unsupported media type')

        # validate body
        errors = CreateTicketCommentSchema().validate(body)
        if errors:
            abort(400, status=400, message=errors)

        try:
            created = TicketService.create_comment(
                key=key,
                body=body,
                attachments=files
            )
            return IssueSchema().dump(created), 201
        except jira.exceptions.JIRAError as ex:
            abort(400, status=400, message=ex.text)


@api.resource('/tickets/supported-boards', endpoint='supported-boards')
class SupportedBoards(Resource):

    def get(self):
        """
        Lists currently supported boards
        ---
        tags:
            - tickets
        responses:
            200:
                description: Ok
                content:
                    application/json:
                        schema:
                            type: array
                            items:
                                type: string
        """
        return jsonify(JiraService.supported_board_keys())


@api.resource('/tickets/supported-categories', endpoint='supported-categories')
class SupportedCategories(Resource):

    def get(self):
        """
        Lists currently supported categories
        ---
        tags:
            - tickets
        responses:
            200:
                description: Ok
                content:
                    application/json:
                        schema:
                            type: array
                            items:
                                type: string
        """
        return jsonify(JiraService.supported_categories())
