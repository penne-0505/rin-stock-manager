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
    IS = auto()
    IN = auto()
    CONTAINS = auto()
    CONTAINED_BY = auto()
    RANGE_GT = auto()
    RANGE_GTE = auto()
    RANGE_LT = auto()
    RANGE_LTE = auto()
    OVERLAPS = auto()


OP_TO_STR = {
    Op.EQ: "eq",
    Op.NEQ: "neq",
    Op.GT: "gt",
    Op.GTE: "gte",
    Op.LT: "lt",
    Op.LTE: "lte",
    Op.LIKE: "like",
    Op.ILIKE: "ilike",
    Op.IS: "is_",
    Op.IN: "in_",
    Op.CONTAINS: "contains",
    Op.CONTAINED_BY: "contained_by",
    Op.RANGE_GT: "range_gt",
    Op.RANGE_GTE: "range_gte",
    Op.RANGE_LT: "range_lt",
    Op.RANGE_LTE: "range_lte",
    Op.OVERLAPS: "overlaps",
}
