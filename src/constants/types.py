from typing import Any, Mapping, Sequence

from constants.filter_op import Op

# Filterの型定義 (例：{"status": (Op.EQ, "active"), "id": (Op.IN, [1,2,3])}
Filter = Mapping[str, tuple[Op, Any | Sequence[Any]]]

# 複合主キーのための、Primary Key (PK) の型定義
PKMap = Mapping[str, Any]
