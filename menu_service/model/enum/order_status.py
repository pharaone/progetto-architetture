import enum


class OrderStatus(enum.Enum):
    SUBMITTED = "Submitted"
    ASSIGNED = "Assigned"
    COMPLETED = "Completed"
    FAILED = "Failed"