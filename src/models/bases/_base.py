from abc import ABC, abstractmethod

from pydantic import BaseModel


class CoreBaseModel(BaseModel, ABC):
    @classmethod
    @abstractmethod
    def __table_name__(cls) -> str: ...
