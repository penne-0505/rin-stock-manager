from enum import Enum, auto


class OrderStatus(Enum):
    PREPARING = auto()
    COMPLETED = auto()
    CANCELED = auto()
