from typing import Any, Iterable, Literal


class QueryFilterUtils:
    """
    Supabaseのクエリフィルタリングユーティリティクラス。
    `client.table('table_name').select('*')`をqueryに渡して使用する。
    """

    @staticmethod
    async def filter_equal(query: Any, column: str, value: Any) -> Any:
        """equalとisは併用不可"""
        query.eq(column, value)
        return query

    @staticmethod
    async def filter_not_equal(query: Any, column: str, value: Any) -> Any:
        """equalとisは併用不可"""
        query.neq(column, value)
        return query

    @staticmethod
    async def filter_grater(query: Any, column: str, value: Any) -> Any:
        query.gt(column, value)
        return query

    @staticmethod
    async def filter_grater_eq(query: Any, column: str, value: Any) -> Any:
        query.gte(column, value)
        return query

    @staticmethod
    async def filter_less(query: Any, column: str, value: Any) -> Any:
        query.lt(column, value)
        return query

    @staticmethod
    async def filter_less_eq(query: Any, column: str, value: Any) -> Any:
        query.lte(column, value)
        return query

    @staticmethod
    async def filter_like(query: Any, column: str, pattern: str) -> Any:
        query.like(column, pattern)
        return query

    @staticmethod
    async def filter_ilike(query: Any, column: str, pattern: str) -> Any:
        """ilikeは大文字小文字を区別しないLIKE検索"""
        query.ilike(column, pattern)
        return query

    @staticmethod
    async def filter_in(query: Any, column: str, values: list[Any]) -> Any:
        query.in_(column, values)
        return query

    @staticmethod
    async def filter_contains(query: Any, column: str, value: Any) -> Any:
        """valueはあらゆるオブジェクトを許容"""
        query.contains(column, value)
        return query

    @staticmethod
    async def filter_contained_by(query: Any, column: str, value: Any) -> Any:
        """valueはあらゆるオブジェクトを許容"""
        query.contained_by(column, value)
        return query

    @staticmethod
    async def filter_range_greater(query: Any, column: str, value: list[Any]) -> Any:
        query.range_gt(column, value)
        return query

    @staticmethod
    async def filter_range_greater_eq(query: Any, column: str, value: list[Any]) -> Any:
        query.range_gte(column, value)
        return query

    @staticmethod
    async def filter_range_less(query: Any, column: str, value: list[Any]) -> Any:
        query.range_lt(column, value)
        return query

    @staticmethod
    async def filter_range_less_eq(query: Any, column: str, value: list[Any]) -> Any:
        query.range_lte(column, value)
        return query

    @staticmethod
    async def filter_range_adjacent(query: Any, column: str, value: list[Any]) -> Any:
        query.range_adjacent(column, value)
        return query

    @staticmethod
    async def filter_overlaps(query: Any, column: str, value: Iterable[Any]) -> Any:
        query.overlaps(column, value)
        return query

    @staticmethod
    async def filter_is(query: Any, column: str, value: Literal["null"] | bool) -> Any:
        """isとequalは併用不可"""
        query.is_(column, value)
        return query

    @staticmethod
    async def filter_match(query: Any, column: str, value: dict[Any, Any]) -> Any:
        query.match(column, value)
        return query
