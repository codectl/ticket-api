from O365.utils import BaseTokenBackend

from src.schemas.token import TokenSchema
from src.services.token import TokenService


class DatabaseTokenBackend(BaseTokenBackend):
    """A token backend based on database entry."""

    def __init__(self):
        super().__init__()

    def load_token(self):
        """Retrieves the token.

        :return dict or None: The token if exists, None otherwise
        """
        token = TokenService.find_by(one=True)
        if token is not None:
            return TokenSchema().dump(token)
        return None

    def save_token(self):
        """Persist the token dict in database."""
        if self.token is None:
            raise ValueError('You have to set the "token" first.')

        # replace older token
        token = TokenService.find_by(one=True)
        if token is not None:
            TokenService.delete(token_id=token.id)

        # ... with the new one
        TokenService.create(**self.token)

        return True

    def delete_token(self):
        """Disable current token."""
        if self.token is None:
            return False

        token = TokenService.find_by(one=True, access_token=self.token.access_token)
        if token is not None:
            TokenService.delete(token_id=token.id)

        return False

    def check_token(self):
        """Check if a token exists in database.
        """
        return TokenService.find_by(one=True) is not None
