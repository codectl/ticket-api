from flask.views import MethodView


class TestView(MethodView):
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
        return {'test': '123'}
