from enum import Enum, auto


class PaymentMethod(Enum):
    CASH = "cash"
    CARD = "card"
    OTHER = "other"


class TransactionType(Enum):
    PURCHASE = "purchase"  # 仕入れ
    SALE = "sale"  # 販売
    ADJUSTMENT = "adjustment"  # 在庫調整
    WASTE = "waste"  # 廃棄


class ReferenceType(Enum):
    ORDER = "order"  # 注文
    PURCHASE = "purchase"  # 仕入れ
    ADJUSTMENT = "adjustment"  # 在庫調整


class UnitType(Enum):
    """在庫管理の単位タイプ"""

    PIECE = "piece"  # 個数管理（厳密）
    GRAM = "gram"  # グラム管理（目安 <- TODO: たまに実際に確認をさせないとだめ？それようの処理？）


class StockLevel(Enum):
    """在庫レベル"""

    SUFFICIENT = "sufficient"  # 在庫あり（緑）
    LOW = "low"  # 在庫少（黄）
    CRITICAL = "critical"  # 緊急（赤）


class FilterOp(Enum):
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
    FilterOp.EQ: "eq",
    FilterOp.NEQ: "neq",
    FilterOp.GT: "gt",
    FilterOp.GTE: "gte",
    FilterOp.LT: "lt",
    FilterOp.LTE: "lte",
    FilterOp.LIKE: "like",
    FilterOp.ILIKE: "ilike",
    FilterOp.IS: "is_",
    FilterOp.IN: "in_",
    FilterOp.CONTAINS: "contains",
    FilterOp.CONTAINED_BY: "contained_by",
    FilterOp.RANGE_GT: "range_gt",
    FilterOp.RANGE_GTE: "range_gte",
    FilterOp.RANGE_LT: "range_lt",
    FilterOp.RANGE_LTE: "range_lte",
    FilterOp.OVERLAPS: "overlaps",
}
