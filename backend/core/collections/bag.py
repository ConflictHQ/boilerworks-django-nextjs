import collections
from typing import Callable, Generic, Iterator, Optional, Tuple, TypeVar

from core.collections.collectors import Collector

K = TypeVar('K')
V = TypeVar('V')


class Bag(Generic[K, V], collections.abc.MutableMapping):

    def __init__(
            self,
            combine: Optional[Callable[[V, V], V]] = None,
            neutral: Optional[Callable[[], V]] = None,
            items: Optional[dict[K, V]] = None):
        self._combine = combine if combine is not None else self._default_combine
        self._neutral = neutral if neutral is not None else self.class_parameters(Bag)[1]
        self._dict = dict() if items is None else dict(items)

    @classmethod
    def class_parameters(cls, target: type) -> tuple[type]:
        attribute = f'_{target.__name__}_parameters'
        if not hasattr(cls, attribute):
            for clazz in cls.__orig_bases__:
                if clazz.__qualname__ == target.__qualname__:
                    setattr(cls, attribute, clazz.__args__)
                    break
        return getattr(cls, attribute)

    def __getitem__(self, key: K) -> V:
        if key not in self._dict and self._neutral is not None:
            self._dict[key] = self._neutral()
        return self._dict[key]

    def __contains__(self, key: K) -> bool:
        return key in self._dict

    def __iter__(self) -> Iterator[Tuple[K, V]]:
        return iter(self._dict.items())

    def __setitem__(self, key: K, value: V):
        if key in self:
            existing_value = self._dict[key]
            new_value = self._combine(existing_value, value)
            self._dict[key] = new_value
        else:
            self._dict[key] = value
        return self

    def __delitem__(self, key: K):
        if key in self:
            del self._dict[key]
        return self

    def __len__(self):
        return len(self._dict)

    def __add__(self, other):
        result = self.__copy__()
        result += self
        result += other
        return self

    def __iadd__(self, other):
        for k, v in other._dict.items():
            self[k] = v
        return self

    def __copy__(self):
        return type(self)(self._combine, self._neutral, self._dict)

    def keys(self) -> Iterator[K]:
        return self._dict.keys()

    def values(self) -> Iterator[V]:
        return self._dict.values()

    def append(self, value: Tuple[K, V]):
        k, v = value
        self[k] = v
        return self

    @classmethod
    def _default_combine(cls, left: V, right: V) -> V:
        left += right
        return left


class BagCollector(Generic[K, V], Collector[Tuple[K, V], Bag[K, V], Bag[K, V]]):

    def __init__(
            self,
            combine: Callable[[V, V], V],
            neutral: Optional[Callable[[], V]],
    ):
        self._combine = combine
        self._neutral = neutral

    def accumulator(self) -> Bag[K, V]:
        return Bag[K, V](self._combine, self._neutral)

    def accumulate(self, accumulator: Bag[K, V], value: Tuple[K, V]) -> Bag[K, V]:
        return accumulator.append(value)

    combine = Bag.__iadd__

    finish = Collector.identity
