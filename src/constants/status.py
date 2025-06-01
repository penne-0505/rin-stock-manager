from enum import Enum


class OrderStatus(Enum):
    PREPARING = "preparing"
    COMPLETED = "completed"
    CANCELED = "canceled"
