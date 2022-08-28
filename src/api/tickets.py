import jira
from flask import Blueprint, request
from flask_restful import Api, Resource

from src import utils
from src.schemas.serializers.jira import Issue
from src.schemas.deserializers import tickets as dsl
from src.services.jira import JiraSvc
from src.services.ticket import TicketSvc

blueprint = Blueprint("tickets", __name__, url_prefix="/tickets")
api = Api(blueprint)


@api.resource("/", endpoint="tickets")
class Tickets(Resource):
    def get(self):
        """
        Get service tickets based on search criteria
        ---
        tags:
            - tickets
        parameters:
            - in: query
              schema: TicketSearchCriteriaSchema
        responses:
            200:
                description: Ok
                content:
                    application/json:
                        schema:
                            type: array
                            items: Issue
            404:
                $ref: "#/components/responses/NotFound"
        """
        params = request.args.copy()
        boards = params.poplist("boards") or (b.key for b in JiraSvc().boards())
        filters = {
            "boards": boards,
            "categories": params.poplist("categories") or JiraSvc.allowed_categories(),
            "fields": params.poplist("fields"),
            "limit": params.get("limit", 20),
            "sort": params.get("sort", "created"),
            **params,
        }

        # validate parameters
        errors = dsl.TicketSearchCriteriaSchema().validate(filters)
        if errors:
            utils.abort_with(400, message=errors)

        # consider default values
        tickets = TicketSvc.find_by(**filters)

        return Issue.IssueSchema(many=True).dump(tickets)

    def post(self):
        """
        Create a new ticket.
        ---
        tags:
            - tickets
        requestBody:
            description: ticket properties
            required: true
            content:
                application/json:
                    schema: CreateTicketSchema
                multipart/form-data:
                    schema: CreateTicketSchemaAttachments
                    encoding:
                        watchers:
                            style: form
                            explode: true
                        attachments:
                            style: form
                            explode: true
        responses:
            201:
                content:
                    application/json:
                        schema: IssueSchema

            400:
                $ref: "#/components/responses/BadRequest"
            415:
                $ref: "#/components/responses/UnsupportedMediaType"
        """
        body = {}
        files = []
        if request.mimetype == "application/json":
            body = request.json
        elif request.mimetype == "multipart/form-data":
            form = request.form.copy()
            form.pop("attachments", default=None)  # ignore this field
            body = {"watchers": form.poplist("watchers"), **form}
            files = request.files.to_dict(flat=False).get("attachments", [])
        else:
            utils.abort_with(415, message="Unsupported media type")

        # validate body
        errors = dsl.CreateTicketSchema().validate(body)
        if errors:
            utils.abort_with(400, message=errors)

        try:
            created = TicketSvc.create(**body, attachments=files)
            return Issue.IssueSchema().dump(created), 201
        except jira.exceptions.JIRAError as ex:
            utils.abort_with(400, message=ex.response.text)


@api.resource("/<key>", endpoint="ticket")
class Ticket(Resource):
    def get(self, key):
        """
        Get ticket given its identifier.
        ---
        tags:
            - tickets
        parameters:
            - in: path
              name: path
              schema:
                type: string
              required: true
              description: the ticket unique identifier
        responses:
            200:
                description: Ok
                content:
                    application/json:
                        schema: IssueSchema
            404:
                $ref: "#/components/responses/NotFound"
        """
        # search for ticket across supported boards and categories
        result = next(
            iter(
                TicketSvc.find_by(
                    key=key,
                    board_keys=(b.key for b in JiraSvc().boards()),
                    categories=JiraSvc.allowed_categories(),
                    limit=1,
                )
            ),
            None,
        )
        if not result:
            utils.abort_with(404, message="Ticket not found")
        else:
            return Issue.IssueSchema().dump(result)


@api.resource("/<key>/comment", endpoint="comment")
class Comment(Resource):
    def post(self, key):
        """
        Create a new ticket comment
        ---
        tags:
            - tickets
        parameters:
            - in: path
              name: path
              schema:
                type: string
              required: true
              description: the ticket unique identifier
        requestBody:
            description: comment properties
            required: true
            content:
                application/json:
                    schema: CreateTicketCommentSchema
                multipart/form-data:
                    schema: CreateTicketCommentSchemaAttachments
                    encoding:
                        watchers:
                            style: form
                            explode: true
                        attachments:
                            style: form
                            explode: true
        responses:
            204:
                description: The resource was created successfully.
            400:
                $ref: "#/components/responses/BadRequest"
            415:
                $ref: "#/components/responses/UnsupportedMediaType"
        """
        body = {}
        files = []
        if request.mimetype == "application/json":
            body = request.json
        elif request.mimetype == "multipart/form-data":
            body = request.form.to_dict(flat=True)
            files = request.files.to_dict(flat=False).get("attachments", [])
        else:
            utils.abort_with(415, message="Unsupported media type")

        # validate body
        errors = dsl.CreateTicketCommentSchema().validate(body)
        if errors:
            utils.abort_with(400, message=errors)

        try:
            TicketSvc.create_comment(issue=key, **body, attachments=files)
            return None, 204
        except jira.exceptions.JIRAError as ex:
            utils.abort_with(400, message=ex.response.text)


@api.resource("/supported-boards", endpoint="supported-boards")
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
        return [b.key for b in JiraSvc().boards()]


@api.resource("/supported-categories", endpoint="supported-categories")
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
        return JiraSvc.allowed_categories()
