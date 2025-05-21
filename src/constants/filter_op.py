from enum import Enum, auto


class Op(Enum):
    EQ = auto()
    NEQ = auto()
    GT = auto()
    GTE = auto()
    LT = auto()
    LTE = auto()
    LIKE = auto()
    ILIKE = auto()
    IS_ = auto()
    IN_ = auto()
    CONTAINS = auto()
    CONTAINED_BY = auto()
    RANGE_GT = auto()
    RANGE_GTE = auto()
    RANGE_LT = auto()
    RANGE_LTE = auto()
    OVERLAPS = auto()
