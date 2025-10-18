import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))


class Settings(BaseSettings):
    KAFKA_BROKERS: str = "localhost:9092"
    ROUTING_SERVICE_URL: str = ""
    GROUP_ID: str = "default_group"
    database_url: str = ""

    model_config = {"env_file": ".env", "env_prefix": ""}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Override KAFKA_BROKERS con KAFKA_BOOTSTRAP_SERVERS se presente
        if os.environ.get('KAFKA_BOOTSTRAP_SERVERS'):
            self.KAFKA_BROKERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS')
