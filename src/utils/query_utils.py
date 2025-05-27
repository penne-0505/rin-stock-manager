from typing import Any

from constants.options import OP_TO_STR, FilterOp
from constants.types import Filter, OrderBy, SimpleFilter
from utils.filters import LogicalCondition, AndCondition, OrCondition, ComplexCondition


def _apply_simple_filters_to_query(query: Any, filters: SimpleFilter) -> Any:
    """従来のシンプルフィルタをクエリに適用"""
    for col, (op, value) in filters.items():
        try:
            method_name = OP_TO_STR[op]
        except KeyError as e:
            raise ValueError(f"Unsupported operator: {op}") from e

        method = getattr(query, method_name, None)
        if method is None:
            raise AttributeError(f"Supabase query has no method {method_name}")

        if op == FilterOp.IN and isinstance(value, (list, tuple, set)):
            value = list(value)

        query = method(col, value if op != FilterOp.IS else "null")
    return query


def _build_or_condition_string(conditions: list[SimpleFilter]) -> str:
    """OR条件用のクエリ文字列を構築"""
    or_parts = []
    for condition_dict in conditions:
        condition_parts = []
        for col, (op, value) in condition_dict.items():
            try:
                method_name = OP_TO_STR[op]
            except KeyError as e:
                raise ValueError(f"Unsupported operator: {op}") from e
            
            if op == FilterOp.IN and isinstance(value, (list, tuple, set)):
                # IN演算子の場合は特別処理
                value_str = ",".join(str(v) for v in value)
                condition_parts.append(f"{col}.{method_name}.({value_str})")
            elif op == FilterOp.IS:
                condition_parts.append(f"{col}.{method_name}.null")
            else:
                condition_parts.append(f"{col}.{method_name}.{value}")
        
        # 単一条件内はANDで結合
        if condition_parts:
            or_parts.append(",".join(condition_parts))
    
    # OR条件で結合
    return ",".join(or_parts)


def apply_filters_to_query(query: Any, filters: Filter) -> Any:
    """統一されたfilter処理（後方互換性を保持）"""
    if isinstance(filters, dict):
        # 従来のSimpleFilter形式
        return _apply_simple_filters_to_query(query, filters)
    
    elif isinstance(filters, LogicalCondition):
        # 新しい論理条件形式
        if isinstance(filters, AndCondition):
            # AND条件は従来通りの処理
            return _apply_simple_filters_to_query(query, filters.conditions)
        
        elif isinstance(filters, OrCondition):
            # OR条件はSupabaseのor()メソッドを使用
            or_string = _build_or_condition_string(filters.conditions)
            return query.or_(or_string)
        
        elif isinstance(filters, ComplexCondition):
            # 複合条件の処理
            if filters.operator == "or":
                # 複合OR条件
                all_conditions = []
                for condition in filters.conditions:
                    if isinstance(condition, AndCondition):
                        all_conditions.append(condition.conditions)
                    elif isinstance(condition, OrCondition):
                        all_conditions.extend(condition.conditions)
                    else:
                        raise ValueError(f"Unsupported condition type in complex OR: {type(condition)}")
                
                or_string = _build_or_condition_string(all_conditions)
                return query.or_(or_string)
            else:
                # 複合AND条件は順次適用
                for condition in filters.conditions:
                    query = apply_filters_to_query(query, condition)
                return query
    
    else:
        raise TypeError(f"Unsupported filter type: {type(filters)}")


def apply_order_by_to_query(query: Any, order_by: OrderBy) -> Any:
    """Supabase クエリに order_by を適用"""
    if isinstance(order_by, tuple):
        col, descending = order_by
        if descending:
            return query.order(col, desc=True)
        return query.order(col, asc=True)
    else:
        # 文字列の場合は昇順
        return query.order(order_by, asc=True)
