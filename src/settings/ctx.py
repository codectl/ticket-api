from werkzeug.exceptions import HTTPException

from flask import current_app
from flask_sqlalchemy import SQLAlchemy

from src import utils

# database session manager
db = SQLAlchemy()


@current_app.errorhandler(HTTPException)
def handle_http_errors(ex):
    """Jsonify http errors."""
    return utils.http_response(ex.code, exclude=("message",)), ex.code
