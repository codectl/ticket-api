import logging
import os

import sqlalchemy as db
from contextlib import contextmanager
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import __main__ as main
from hpdasupport.config import Config
from manager import Manager


def logging_settings():
    """ Setting up logging properties. """

    logging.basicConfig(handlers=[logging.StreamHandler()], level=logging.INFO)
    logging.getLogger('O365').setLevel(logging.WARNING)


def config_from_object(obj):
    return dict((v, getattr(obj, v)) for v in dir(obj))


logging_settings()

# Configuration setup
config = config_from_object(Config())

# Application manager
manager = Manager()

Base = declarative_base()
session = None


def database_setup():
    """ Setting up database. """

    # Initialize SQLite database
    root_path = os.path.dirname(os.path.realpath(main.__file__))
    database_uri = 'sqlite:///' + os.path.join(root_path, 'database.db')
    engine = db.create_engine(database_uri)

    # SqlAlchemy session setup
    Session = sessionmaker(bind=engine)

    # Create all tables that do not already exist
    Base.metadata.create_all(engine)

    # Start new SQLAlchemy session
    global session
    session = Session()


@contextmanager
def session_scope():
    """ Provide a transactional scope around a series of operations. """

    global session
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
