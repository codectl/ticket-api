from typing import Optional, Union, List

from flask import current_app

from src import db
from src.models.OAuth2Token import OAuth2Token


class TokenService:

    @staticmethod
    def create(**kwargs) -> OAuth2Token:
        token = OAuth2Token(**kwargs)

        db.session.add(token)
        db.session.commit()

        current_app.logger.debug("Created token '{0}'.".format(token.access_token))

        return token

    @staticmethod
    def get(token_id) -> Optional[OAuth2Token]:
        return OAuth2Token.query.get(token_id)

    @staticmethod
    def find_by(one=False, **filters) -> Union[List[OAuth2Token], Optional[OAuth2Token]]:
        query = OAuth2Token.query.filter_by(**filters)
        return query.all() if not one else query.one_or_none()

    @classmethod
    def update(cls, token_id, **kwargs):
        token = cls.get(token_id=token_id)
        for key, value in kwargs.items():
            if hasattr(token, key):
                setattr(token, key, value)
        db.session.commit()

        current_app.logger.info("Updated token '{0}' with the following attributes: '{1}'."
                                .format(token.access_token, kwargs))

    @classmethod
    def delete(cls, token_id):
        token = cls.get(token_id=token_id)
        if token:
            db.session.delete(token)
            db.session.commit()

            current_app.logger.debug("Deleted token '{0}'.".format(token.access_token))
