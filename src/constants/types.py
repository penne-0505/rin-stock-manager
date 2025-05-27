from typing import TYPE_CHECKING, Any, Mapping, Sequence, Union

from constants.options import FilterOp

if TYPE_CHECKING:
    from utils.filters import LogicalCondition

# 基本的なフィルタ条件（従来の型）
SimpleFilter = Mapping[str, tuple[FilterOp, Any | Sequence[Any]]]

# 後方互換維持しつつ統合されたフィルタ😁
Filter = Union[SimpleFilter, "LogicalCondition"]

# 複合主キーのための、Primary Key (PK) の型定義
PKMap = Mapping[str, Any]

# OrderByの型定義。単一の列名または (列名, 降順フラグ)
OrderBy = str | tuple[str, bool]
