from enum import Enum


class StatusEnum(str, Enum):
    PENDING = "pending"
    RECEIVED = "received"
    PREPARING = "preparing"
    READY_FOR_PICKUP = "ready_for_pickup"
    COMPLETED = "completed"
    CANCELLED = "cancelled"