import typing

from flask import current_app

from src import db
from src.models.tokens import OAuth2Token


class TokenSvc:
    @staticmethod
    def create(**kwargs) -> OAuth2Token:
        token = OAuth2Token(**kwargs)

        db.session.add(token)
        db.session.commit()

        current_app.logger.debug(f"Created token '{token.access_token}'.")

        return token

    @staticmethod
    def get(token_id) -> typing.Optional[OAuth2Token]:
        return OAuth2Token.query.get(token_id)

    @staticmethod
    def find_by(
        one=False, **filters
    ) -> typing.Union[list[OAuth2Token], typing.Optional[OAuth2Token]]:
        query = OAuth2Token.query.filter_by(**filters)
        return query.all() if not one else query.one_or_none()

    @classmethod
    def update(cls, token_id, **kwargs):
        token = cls.get(token_id=token_id)
        for key, value in kwargs.items():
            if hasattr(token, key):
                setattr(token, key, value)
        db.session.commit()

        access_token = token.access_token
        msg = f"Updated token '{access_token}' with the attributes: '{kwargs}'."
        current_app.logger.info(msg)

    @classmethod
    def delete(cls, token_id):
        token = cls.get(token_id=token_id)
        if token:
            db.session.delete(token)
            db.session.commit()

            current_app.logger.debug(f"Deleted token '{token.access_token}'.")
