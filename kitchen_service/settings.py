# settings.py
import uuid
from typing import List, Optional, Tuple
from pydantic_settings import BaseSettings
from pydantic import Field
from pydantic.networks import AnyUrl   # (o: from pydantic import AnyUrl; entrambe funzionano con v2)
from uuid import UUID

class Settings(BaseSettings):
    HOST: str = Field("0.0.0.0", env="HOST")
    PORT: int = Field(8000, env="PORT")
    API_PREFIX: str = Field("/api", env="API_PREFIX")
    # backward-compatible single var (if you set KAFKA_BROKERS explicitly)
    KAFKA_BROKERS_RAW: Optional[str] = Field(None, env="KAFKA_BROKERS_RAW")
    # recommended: two distinct vars for internal (container) and external (host) use
    KAFKA_BROKERS_INTERNAL: str = Field("kafka:29092", env="KAFKA_BROKERS_INTERNAL")
    KAFKA_BROKERS_EXTERNAL: str = Field("localhost:9092", env="KAFKA_BROKERS_EXTERNAL")

    ETCD_HOST: str = Field("localhost", env="ETCD_HOST")
    ETCD_PORT: int = Field(2379, env="ETCD_PORT")
    INTERNAL_API_KEY: str = Field("changeme123", env="INTERNAL_API_KEY")
    REDIS_CLUSTER_NODES: str = Field("localhost:7000,localhost:7001,localhost:7002", env="REDIS_CLUSTER_NODES")
    KITCHEN_ID: UUID = Field(default_factory=uuid.uuid4, env="KITCHEN_ID") #KITCHEN_ID: Optional[UUID] = Field(None, env="KITCHEN_ID")
    WORKERS: int = Field(1, env="WORKERS")

    @property
    def KAFKA_BROKERS(self) -> str:
        """
        Compat property used by the app:
        precedence:
          1) KAFKA_BROKERS_RAW (legacy single var, if set)
          2) KAFKA_BROKERS_INTERNAL (recommended for containers)
          3) KAFKA_BROKERS_EXTERNAL (host fallback)
        """
        raw = (self.KAFKA_BROKERS_RAW or "").strip()
        if raw:
            return raw
        # prefer internal for services running in Docker; fall back to external
        return self.KAFKA_BROKERS_INTERNAL or self.KAFKA_BROKERS_EXTERNAL

    def redis_nodes(self) -> List[Tuple[str, int]]:
        """Parse REDIS_CLUSTER_NODES -> [(host, port), ...]"""
        nodes = []
        for part in self.REDIS_CLUSTER_NODES.split(","):
            host_port = part.strip().split(":")
            if len(host_port) != 2:
                raise ValueError("REDIS_CLUSTER_NODES deve essere host:port[,host2:port2...]")
            host, port = host_port
            nodes.append((host.strip(), int(port.strip())))
        return nodes

# crea un'istanza condivisa (singleton)
settings = Settings()
