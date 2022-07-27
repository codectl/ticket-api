from src.settings.ctx import db


class AccessToken(db.Model):
    __tablename__ = "access_tokens"

    id = db.Column(db.Integer, primary_key=True)
    token_type = db.Column(db.String, nullable=False)
    scope = db.ARRAY(db.String())
    access_token = db.Column(db.String, nullable=False, unique=True)
    refresh_token = db.Column(db.String, nullable=False, unique=True)
    expires_in = db.Column(db.Integer, nullable=False)
    ext_expires_in = db.Column(db.Integer, nullable=False)
    expires_at = db.Column(db.Float, nullable=False)
