"""
Modulo di configurazione per l'applicazione.
Utilizza Pydantic per caricare le impostazioni dall'ambiente.
"""
import uuid
from typing import List, Optional, Tuple
from uuid import UUID

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Definisce le impostazioni di configurazione caricate da variabili d'ambiente.
    """
    HOST: str = Field("0.0.0.0", env="HOST")
    PORT: int = Field(8000, env="PORT")
    API_PREFIX: str = Field("/api", env="API_PREFIX")

    # Per compatibilità all'indietro con una singola variabile KAFKA_BROKERS
    KAFKA_BROKERS_RAW: Optional[str] = Field(None, env="KAFKA_BROKERS_RAW")
    
    # Impostazioni raccomandate: due variabili distinte per l'uso interno (container) ed esterno (host)
    KAFKA_BROKERS_INTERNAL: str = Field("kafka:29092", env="KAFKA_BROKERS_INTERNAL")
    KAFKA_BROKERS_EXTERNAL: str = Field("localhost:9092", env="KAFKA_BROKERS_EXTERNAL")

    ETCD_HOST: str = Field("localhost", env="ETCD_HOST")
    ETCD_PORT: int = Field(2379, env="ETCD_PORT")
    INTERNAL_API_KEY: str = Field("changeme123", env="INTERNAL_API_KEY")
    REDIS_CLUSTER_NODES: str = Field("localhost:7000,localhost:7001,localhost:7002", env="REDIS_CLUSTER_NODES")
    
    # Correzione: KITCHEN_ID ora ha un tipo (UUID) e un valore di default generato dinamicamente
    # se non viene fornito tramite variabile d'ambiente.
    KITCHEN_ID: UUID = Field(default_factory=uuid.uuid4, env="KITCHEN_ID")
    
    WORKERS: int = Field(1, env="WORKERS")

    @property
    def KAFKA_BROKERS(self) -> str:
        """
        Proprietà calcolata per ottenere i broker Kafka con la giusta priorità.
        1. KAFKA_BROKERS_RAW (se impostato, per retrocompatibilità)
        2. KAFKA_BROKERS_INTERNAL (consigliato per container)
        3. KAFKA_BROKERS_EXTERNAL (fallback per esecuzione locale)
        """
        raw = (self.KAFKA_BROKERS_RAW or "").strip()
        if raw:
            return raw
        return self.KAFKA_BROKERS_INTERNAL or self.KAFKA_BROKERS_EXTERNAL

    def get_redis_nodes(self) -> List[Tuple[str, int]]:
        """
        Esegue il parsing della stringa REDIS_CLUSTER_NODES in una lista di tuple (host, porta).
        """
        nodes = []
        for part in self.REDIS_CLUSTER_NODES.split(","):
            host_port = part.strip().split(":")
            if len(host_port) != 2:
                raise ValueError("REDIS_CLUSTER_NODES deve essere nel formato host:port[,host2:port2...]")
            host, port = host_port
            nodes.append((host.strip(), int(port.strip())))
        return nodes

# Crea un'istanza condivisa (singleton) da importare in altre parti dell'app
settings = Settings()
