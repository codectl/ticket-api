from hpdasupport import Base

from sqlalchemy import Column, Integer, String, DateTime


class OAuth2(Base):
    __tablename__ = "oauth2"

    id = Column(Integer, primary_key=True)
    authorization_code = Column(String)
    access_token = Column(String)
    refresh_token = Column(String)
    expires_on = Column(DateTime)
    user_email = Column(String, index=True, unique=True, nullable=False)
    token_type = Column(String)
    resource = Column(String)
    scope = Column(String)
