from core.collections.histogram import HistogramCollector
from core.collections.tests.data import days_number


def test_histogram():
    collector = HistogramCollector[str]()
    histogram = collector([day for day, _number in days_number])

    assert dict(histogram) == {
        'A Sun': 4,
        'B Mon': 4,
        'C Tue': 5,
        'D Wed': 5,
        'E Thu': 5,
        'F Fri': 4,
        'G Sat': 4,
    }

    assert histogram['H Oct'] == 0

    assert dict(histogram) == {
        'A Sun': 4,
        'B Mon': 4,
        'C Tue': 5,
        'D Wed': 5,
        'E Thu': 5,
        'F Fri': 4,
        'G Sat': 4,
        'H Oct': 0,
    }
