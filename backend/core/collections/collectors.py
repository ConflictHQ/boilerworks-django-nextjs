import abc
from typing import Generic, Iterable, TypeVar

T = TypeVar('T')
A = TypeVar('A')
R = TypeVar('R')


class Collector(abc.ABC, Generic[T, A, R]):

    @abc.abstractmethod
    def accumulator(self):
        ...

    @abc.abstractmethod
    def accumulate(self, accumulator: A, value: T) -> A:
        ...

    @abc.abstractmethod
    def combine(self, left: A, right: A) -> A:
        ...

    @abc.abstractmethod
    def finish(self, accumulator: A) -> R:
        ...

    @classmethod
    def identity(cls, accumulator: A) -> A:
        return accumulator

    def __call__(self, iterable: Iterable[T]) -> R:
        accumulator: A = self.accumulator()
        for value in iterable:
            accumulator = self.accumulate(accumulator, value)
        result = self.finish(accumulator)
        return result
