from datetime import date, datetime, timedelta


class DateInterval:

    def __init__(self, lower_bound: datetime, upper_bound: datetime):
        self._lower_bound = min(lower_bound, upper_bound)
        self._upper_bound = max(lower_bound, upper_bound)
        self._days = (self._upper_bound - self._lower_bound).days + 1

    @property
    def lower_date(self) -> date:
        return self._lower_bound.date()

    @property
    def upper_date(self) -> date:
        return self._upper_bound.date()

    @property
    def lower_datetime(self) -> datetime:
        return self._lower_bound

    @property
    def upper_datetime(self) -> datetime:
        return self._upper_bound

    def __str__(self):
        return f'[{self.lower_date}-{self.upper_date}]'

    def __repr__(self):
        return f'{self.lower_date}:{self.upper_date}'

    def __len__(self) -> int:
        return self._days

    def __iter__(self):
        days = [
            (self._lower_bound + timedelta(days=days)).date()
            for days in range(self._days)
        ]
        return iter(days)
