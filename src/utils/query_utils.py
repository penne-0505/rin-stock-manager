from typing import Any

from constants.filter_op import OP_TO_STR, Op
from constants.types import Filter


def apply_filters_to_query(query: Any, filters: Filter) -> Any:
    for col, (op, value) in filters.items():
        try:
            method_name = OP_TO_STR[op]
        except KeyError as e:
            raise ValueError(f"Unsupported operator: {op}") from e

        method = getattr(query, method_name, None)
        if method is None:
            raise AttributeError(f"Supabase query has no method {method_name}")

        if op == Op.IN_ and isinstance(value, (list, tuple, set)):
            value = list(value)

        query = method(col, value if op != Op.IS_ else "null")
    return query
