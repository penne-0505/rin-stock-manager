from __future__ import annotations

import datetime
from collections.abc import Mapping, Sequence
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

from models.bases._base import CoreBaseModel


def _is_supabase_compatible(value: Any) -> bool:
    """Supabaseに対応している型かどうかを判定"""
    if value is None:
        return True
    
    # Supabaseに対応している基本型
    if isinstance(value, (str, int, float, bool)):
        return True
    
    # Supabaseに対応している日時型
    if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
        return True
    
    # その他の対応型
    if isinstance(value, (list, dict)):
        return True
    
    return False


def _serialize_value(value: Any) -> Any:
    """Supabase非対応型を対応型にシリアライズ"""
    if value is None:
        return None
    
    # 既にSupabase対応型の場合はそのまま返す
    if _is_supabase_compatible(value):
        # リストや辞書の場合は再帰的にチェック
        if isinstance(value, list):
            return [_serialize_value(item) for item in value]
        elif isinstance(value, dict):
            return {k: _serialize_value(v) for k, v in value.items()}
        return value
    
    # Enum型のシリアライズ
    if isinstance(value, Enum):
        return value.value
    
    # UUID型のシリアライズ
    if isinstance(value, UUID):
        return str(value)
    
    # Decimal型のシリアライズ
    if isinstance(value, Decimal):
        return float(value)
    
    # Pydanticモデルのシリアライズ
    if isinstance(value, CoreBaseModel):
        return serialize_for_supabase(value.model_dump())
    
    # その他のオブジェクト（__dict__がある場合）
    if hasattr(value, "__dict__"):
        return serialize_for_supabase(value.__dict__)
    
    # 最終的に文字列に変換
    return str(value)


def serialize_for_supabase(data: Mapping[str, Any] | CoreBaseModel) -> dict[str, Any]:
    """
    PydanticモデルまたはdictをSupabase用にシリアライズ
    
    Args:
        data: シリアライズ対象のデータ（PydanticモデルまたはMapping）
        
    Returns:
        Supabaseに保存可能な形式のdict
        
    Raises:
        TypeError: 不正な型が渡された場合
    """
    if isinstance(data, CoreBaseModel):
        source_dict = data.model_dump()
    elif isinstance(data, Mapping):
        source_dict = dict(data)
    else:
        raise TypeError(f"Expected CoreBaseModel or Mapping, got {type(data)}")
    
    return {key: _serialize_value(value) for key, value in source_dict.items()}


def bulk_serialize_for_supabase(
    items: Sequence[Mapping[str, Any] | CoreBaseModel]
) -> list[dict[str, Any]]:
    """
    複数のアイテムを一括でSupabase用にシリアライズ
    
    Args:
        items: シリアライズ対象のアイテムリスト
        
    Returns:
        Supabaseに保存可能な形式のdictのリスト
    """
    return [serialize_for_supabase(item) for item in items]