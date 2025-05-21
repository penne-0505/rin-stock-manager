from typing import Any

from constants.filter_op import Op
from constants.types import Filter


def apply_filters_to_query(
    query: Any, filters: Filter
) -> Any:  # Anyだが、AsyncSelectRequestBuilderであるはず <- これ、型指定する？
    for col, (op, value) in filters.items():
        method_name = op.name.lower()
        if hasattr(query, method_name):
            method_to_call = getattr(query, method_name)
            if op == Op.IS_:
                query = method_to_call(col, "null")
            else:
                query = method_to_call(col, value)
        else:
            # 普通ありえない。ここにたどり着く場合、フィルタの定義が間違っている？
            # エラー投げる？
            pass
    return query
