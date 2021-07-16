from O365.utils import BaseTokenBackend

from src.services.token import TokenService
from src.serializers.token import TokenSchema


class DatabaseTokenBackend(BaseTokenBackend):
    """A token backend based on database entry."""

    def __init__(self):
        super().__init__()

    def load_token(self):
        """Retrieves the token.

        :return dict or None: The token if exists, None otherwise
        """
        token = TokenService.find_by(one=True, active=True)
        if token is not None:
            return TokenSchema().dump(token)
        return None

    def save_token(self):
        """Persist the token dict in database."""
        if self.token is None:
            raise ValueError('You have to set the "token" first.')

        TokenService.create(**self.token, active=True)

        return True

    def delete_token(self):
        """Disable current token."""
        if self.token is None:
            return False

        token = TokenService.find_by(one=True, access_token=self.token.access_token, active=True)
        if token is not None:
            TokenService.update(token_id=token.id, active=False)

        return False

    def check_token(self):
        """Check if the active token exists in database.

        :return bool: True if exists, False otherwise
        """
        return TokenService.find_by(one=True, active=True) is not None
