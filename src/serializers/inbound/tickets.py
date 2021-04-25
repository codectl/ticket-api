from flask import current_app
from marshmallow import Schema, fields, validate, ValidationError

from src.services.jira import JiraService


class TicketSearchCriteria(Schema):
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

    boards = fields.List(
        fields.String(
            validate=validate.OneOf(JiraService.supported_board_keys()),
        ),
        missing= [current_app.config['JIRA_DEFAULT_BOARD']['key']],
        description='boards to fetch tickets from',
        explode=False,
    )
    message = fields.String()
