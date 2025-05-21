from typing import Any

from constants.filter_op import Op
from constants.types import Filter


def apply_filters_to_query(query: Any, filters: Filter) -> Any:
    for col, (op, value) in filters.items():
        method_name = op.name.lower()
        if hasattr(query, method_name):
            method_to_call = getattr(query, method_name)
            if op == Op.IS_:
                query = method_to_call(col, "null")
            else:
                query = method_to_call(col, value)
        else:
            raise ValueError(f"Unsupported operation: {op}")
    return query
