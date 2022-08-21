import base64

from flask_restful import abort
from werkzeug.http import HTTP_STATUS_CODES

from src.schemas.serializers.http import HttpResponseSchema
from src.settings import oas


def http_response(code: int, message="", serialize=True, **kwargs):
    response = oas.HttpResponse(
        code=code, reason=HTTP_STATUS_CODES[code], message=message
    )
    if serialize:
        return HttpResponseSchema(**kwargs).dump(response)
    return response


def abort_with(code: int, message=""):
    abort(code, **http_response(code, message=message))


def encode_content(content):
    """Convert img src to base64 content bytes."""
    data = base64.b64encode(content)  # encode to base64 (bytes)
    data = data.decode()  # convert bytes to string

    return data
