from fastapi import Depends
from sqlalchemy.orm import Session

from menu_service.config.settings import Settings
from menu_service.db.session_manager import SessionManager


def get_settings():
    return Settings()


def get_session(settings: Settings = Depends(get_settings)):
    return SessionManager(settings)


def get_db(
        session: SessionManager = Depends(get_session)
) -> Session:
    db = session.session_local()
    try:
        yield db
    finally:
        db.close()
