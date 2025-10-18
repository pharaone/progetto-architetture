from fastapi import Depends
from sqlalchemy.orm import Session

from config.settings import Settings
from db.session_manager import SessionManager

from db.base import Base


def get_settings():
    return Settings()


def get_session(settings: Settings = Depends(get_settings)):
    return SessionManager(settings)


def get_db(
        session: SessionManager = Depends(get_session)
) -> Session:
    db = session.session_local()
    Base.metadata.create_all(bind=session.engine)
    try:
        yield db
    finally:
        db.close()
