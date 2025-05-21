from abc import ABC, abstractmethod

from pydantic import BaseModel


class CoreBaseModel(BaseModel, ABC):
    @abstractmethod
    def __table_name__(self) -> str:
        pass
