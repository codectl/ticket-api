from src import db


class OAuth2Token(db.Model):
    __tablename__ = 'oauth2_tokens'

    id = db.Column(db.Integer, primary_key=True)
    token_type = db.Column(db.String, nullable=False)
    scope = db.ARRAY(db.String())
    access_token = db.Column(db.String, nullable=False, unique=True)
    refresh_token = db.Column(db.String, nullable=False, unique=True)
    expires_in = db.Column(db.Integer, nullable=False)
    ext_expires_in = db.Column(db.Integer, nullable=False)
    expires_at = db.Column(db.Float, nullable=False)
    active = db.Column(db.Boolean, nullable=False)
