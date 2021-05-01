import flasgger.marshmallow_apispec as apispec
from apispec.ext.marshmallow.openapi import OpenAPIConverter


class OpenAPI3Converter(OpenAPIConverter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


def openapi3_converters():
    """
    Force flasgger to use an OpenAPI3 marshmallow schema converter
    """
    openapi_converter = OpenAPI3Converter(
        openapi_version='3.0',
        schema_name_resolver=lambda schema: None,
        spec=None
    )
    # Overwrite functions in Flasgger module
    apispec.schema2jsonschema = openapi_converter.schema2jsonschema
    apispec.schema2parameters = openapi_converter.schema2parameters
