from typing import Generic

from .bag import Bag, K
from .collectors import Collector, T


class Histogram(Generic[K], Bag[K, int]):
    pass


class RealHistogram(Generic[K], Bag[K, float]):
    pass


class HistogramCollector(Generic[T], Collector[T, Histogram[T], Histogram[T]]):

    def accumulate(self, accumulator: Histogram[T], value: T) -> Histogram[T]:
        accumulator[value] = 1
        return accumulator

    accumulator = Histogram
    combine = Histogram.__iadd__
    finish = Collector.identity
