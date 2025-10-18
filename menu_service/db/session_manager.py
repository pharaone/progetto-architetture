from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pymysql

from config.settings import Settings


class SessionManager:
    def __init__(self, settings: Settings):
        self.database_url = settings.database_url
        self.engine = create_engine(self.database_url, pool_pre_ping=True, pool_size=20)
        self.session_local = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
