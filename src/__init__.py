from importlib import metadata

__meta__ = metadata.metadata("ticket-api")
__version__ = __meta__["version"]
