from O365.utils import BaseTokenBackend

from src.schemas.token import TokenSchema
from src.services.token import TokenSvc


class DatabaseTokenBackend(BaseTokenBackend):
    """A token backend based on database entry."""

    def load_token(self):
        token = TokenSvc.find_by(one=True)
        if token is not None:
            return TokenSchema().dump(token)
        return None

    def save_token(self):
        if self.token is None:
            raise ValueError("You have to set the 'token' first.")

        svc = TokenSvc()

        # replace older token
        token = svc.find_by(one=True)
        if token is not None:
            svc.delete(token_id=token.id)

        # ... with the new one
        svc.create(**self.token)

        return True

    def delete_token(self):
        """Disable current token."""
        if self.token is None:
            return False

        svc = TokenSvc()
        token = svc.find_by(one=True, access_token=self.token.access_token)
        if token is not None:
            svc.delete(token_id=token.id)

        return False

    def check_token(self):
        return TokenSvc.find_by(one=True) is not None
