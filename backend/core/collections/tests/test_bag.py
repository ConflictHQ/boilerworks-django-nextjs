from core.collections.bag import Bag, BagCollector
from core.collections.tests.data import days_number


def test_bag_as_set_collection():
    collector = BagCollector[str, set](set.union, int)
    bag: Bag[str, set] = collector([(day, {number}) for day, number in days_number])
    assert dict(bag) == {
        'C Tue': {0, 7, 14, 21, 28},
        'D Wed': {1, 8, 15, 22, 29},
        'E Thu': {2, 9, 16, 23, 30},
        'F Fri': {3, 10, 17, 24},
        'G Sat': {4, 11, 18, 25},
        'A Sun': {5, 12, 19, 26},
        'B Mon': {6, 13, 20, 27},
    }
