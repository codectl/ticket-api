from flask import current_app, redirect, request, url_for
from flask_restplus import Namespace, Resource


service = Namespace(
    'service',
    description='Manage service tickets.'
)


@service.route('/')
class Service(Resource):

    def get(self):
        """
        Get service tickets based on search criteria.
        """
        current_app.logger.info('1111111')
        return { 'status': 200 }

    # def post(self):
    #     confirmed = request.form['confirm']
    #     if confirmed:
    #         # Granted by resource owner
    #         return authorization.create_authorization_response(grant_user=current_user)
    #
    #     # Denied by resource owner
    #     return authorization.create_authorization_response(grant_user=None)
