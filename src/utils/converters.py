import base64

import flasgger.marshmallow_apispec as apispec
from apispec.ext.marshmallow.openapi import OpenAPIConverter


class OpenAPI3Converter(OpenAPIConverter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


def openapi3_converters():
    """Force flasgger to use an OpenAPI3 marshmallow schema converter."""
    openapi_converter = OpenAPI3Converter(
        openapi_version='3.0',
        schema_name_resolver=lambda schema: None,
        spec=None
    )
    # Overwrite functions in Flasgger module
    apispec.schema2jsonschema = openapi_converter.schema2jsonschema
    apispec.schema2parameters = openapi_converter.schema2parameters


def encode_content(content):
    """Convert img src to base64 content bytes."""
    data = base64.b64encode(content)  # encode to base64 (bytes)
    data = data.decode()  # convert bytes to string

    return data
