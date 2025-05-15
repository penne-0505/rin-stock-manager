from typing import Any, Iterable, Literal


class QueryFilterUtils:
    """
    Supabaseのクエリフィルタリングユーティリティクラス。
    `client.table('table_name').select('*')`をqueryに渡して使用する。
    """

    @staticmethod
    async def filter_equal(base_query: Any, column: str, value: Any) -> Any:
        """equalとisは併用不可"""
        base_query.eq(column, value)
        return base_query

    @staticmethod
    async def filter_not_equal(base_query: Any, column: str, value: Any) -> Any:
        """equalとisは併用不可"""
        base_query.neq(column, value)
        return base_query

    @staticmethod
    async def filter_grater(base_query: Any, column: str, value: Any) -> Any:
        base_query.gt(column, value)
        return base_query

    @staticmethod
    async def filter_grater_eq(base_query: Any, column: str, value: Any) -> Any:
        base_query.gte(column, value)
        return base_query

    @staticmethod
    async def filter_less(base_query: Any, column: str, value: Any) -> Any:
        base_query.lt(column, value)
        return base_query

    @staticmethod
    async def filter_less_eq(base_query: Any, column: str, value: Any) -> Any:
        base_query.lte(column, value)
        return base_query

    @staticmethod
    async def filter_like(base_query: Any, column: str, pattern: str) -> Any:
        base_query.like(column, pattern)
        return base_query

    @staticmethod
    async def filter_ilike(base_query: Any, column: str, pattern: str) -> Any:
        """ilikeは大文字小文字を区別しないLIKE検索"""
        base_query.ilike(column, pattern)
        return base_query

    @staticmethod
    async def filter_in(base_query: Any, column: str, values: list[Any]) -> Any:
        base_query.in_(column, values)
        return base_query

    @staticmethod
    async def filter_contains(base_query: Any, column: str, value: Any) -> Any:
        """valueはあらゆるオブジェクトを許容"""
        base_query.contains(column, value)
        return base_query

    @staticmethod
    async def filter_contained_by(base_query: Any, column: str, value: Any) -> Any:
        """valueはあらゆるオブジェクトを許容"""
        base_query.contained_by(column, value)
        return base_query

    @staticmethod
    async def filter_range_greater(
        base_query: Any, column: str, value: list[Any]
    ) -> Any:
        base_query.range_gt(column, value)
        return base_query

    @staticmethod
    async def filter_range_greater_eq(
        base_query: Any, column: str, value: list[Any]
    ) -> Any:
        base_query.range_gte(column, value)
        return base_query

    @staticmethod
    async def filter_range_less(base_query: Any, column: str, value: list[Any]) -> Any:
        base_query.range_lt(column, value)
        return base_query

    @staticmethod
    async def filter_range_less_eq(
        base_query: Any, column: str, value: list[Any]
    ) -> Any:
        base_query.range_lte(column, value)
        return base_query

    @staticmethod
    async def filter_range_adjacent(
        base_query: Any, column: str, value: list[Any]
    ) -> Any:
        base_query.range_adjacent(column, value)
        return base_query

    @staticmethod
    async def filter_overlaps(
        base_query: Any, column: str, value: Iterable[Any]
    ) -> Any:
        base_query.overlaps(column, value)
        return base_query

    @staticmethod
    async def filter_is(
        base_query: Any, column: str, value: Literal["null"] | bool
    ) -> Any:
        """isとequalは併用不可"""
        base_query.is_(column, value)
        return base_query

    @staticmethod
    async def filter_match(base_query: Any, column: str, value: dict[Any, Any]) -> Any:
        base_query.match(column, value)
        return base_query
