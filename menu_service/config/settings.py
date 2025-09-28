import os

from dotenv import load_dotenv
from pydantic.v1 import BaseSettings

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))


class Settings(BaseSettings):
    KAFKA_BROKERS: str = os.environ.get("KAFKA_BROKERS")
    ROUTING_SERVICE_URL: str = os.environ.get("ROUTING_SERVICE_URL")
    GROUP_ID: str = os.environ.get("GROUP_ID")
    database_url: str = os.environ.get("DATABASE_URL")

    class Config:
        env_file = ".env"
