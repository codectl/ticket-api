from flask_restful import Resource


class Test(Resource):
    def get(self):
        """
        Example endpoint returning a list of colors by palette
        This is using docstrings for specifications.
        ---
        tags:
            - test
        responses:
          200:
            description: Ok
        """
        return {'status': 'ok'}
