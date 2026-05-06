from abc import ABC, abstractmethod


class BaseTree(ABC):
    order: int
    split_count: int

    @abstractmethod
    def search(self, key: int): ...

    @abstractmethod
    def insert(self, key: int, record_id: int) -> None: ...

    @abstractmethod
    def delete(self, key: int) -> bool: ...

    @abstractmethod
    def node_count(self) -> int: ...

    @abstractmethod
    def utilization(self) -> float: ...
