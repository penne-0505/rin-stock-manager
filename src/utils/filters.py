from typing import Any
from abc import ABC, abstractmethod

from constants.types import SimpleFilter


class LogicalCondition(ABC):
    """論理演算子の基底クラス"""
    
    @abstractmethod
    def to_supabase_filter(self) -> dict[str, Any]:
        """Supabaseクエリ用のフィルタ辞書に変換"""
        pass


class AndCondition(LogicalCondition):
    """AND条件（デフォルトの動作）"""
    
    def __init__(self, conditions: SimpleFilter):
        self.conditions = conditions
    
    def to_supabase_filter(self) -> dict[str, Any]:
        return {"type": "and", "conditions": self.conditions}


class OrCondition(LogicalCondition):
    """OR条件"""
    
    def __init__(self, conditions: list[SimpleFilter]):
        self.conditions = conditions
    
    def to_supabase_filter(self) -> dict[str, Any]:
        return {"type": "or", "conditions": self.conditions}


class ComplexCondition(LogicalCondition):
    """複合条件（AND/ORの組み合わせ）"""
    
    def __init__(self, conditions: list[LogicalCondition], operator: str = "and"):
        self.conditions = conditions
        self.operator = operator  # "and" or "or"
    
    def to_supabase_filter(self) -> dict[str, Any]:
        return {
            "type": "complex",
            "operator": self.operator,
            "conditions": [c.to_supabase_filter() for c in self.conditions]
        }