from collections import defaultdict
from datetime import date as Date
from datetime import timedelta
from typing import Iterable, Iterator

from core.utils.datetime_truncate import truncate
from django.db import models
from django.db.models import QuerySet

from .enum import BaseEnumModel, EnumModel, register_for_model


class Interval(EnumModel):
    duration = models.CharField(max_length=64, unique=False)
    unit = models.CharField(max_length=64, null=False, blank=False)
    pay_period = models.BooleanField(null=False, blank=False, default=False)


class PeriodQuerySet(QuerySet):

    def filter_by_date(self, date: Date) -> "PeriodQuerySet":
        return self.filter(lower_bound__gte=date, upper_bound__lte=date, )

    def intersects(self, date: Date) -> "PeriodQuerySet":
        return self.exclude(lower_bound__gt=date).exclude(upper_bound__lt=date)

    def filter_by_pay_period(self, pay_period: bool = True) -> "PeriodQuerySet":
        return self.filter(pay_period=pay_period, )

    def filter_by_interval(self, interval: Interval) -> "PeriodQuerySet":
        return self.filter(interval=interval)


class Period(models.Model):
    class Meta:
        ordering = 'interval__ordinal', '-lower_bound'

    objects = PeriodQuerySet.as_manager()
    period = models.CharField(max_length=64, primary_key=True)
    interval = models.ForeignKey(Interval, on_delete=models.CASCADE)
    lower_bound = models.DateField(null=False, blank=False)
    upper_bound = models.DateField(null=False, blank=False)
    pay_period = models.BooleanField(null=False, blank=False, default=False)

    @property
    def range(self) -> tuple[Date, Date]:
        return self.lower_bound, self.upper_bound

    def intersects(self, lower_bound: Date, upper_bound: Date) -> bool:
        if upper_bound < self.lower_bound:
            return False
        if lower_bound > self.upper_bound:
            return False
        return True

    def iterate(self, interval: Interval) -> Iterator["Period"]:
        lower_bound, upper_bound = self.range
        diff = timedelta(days=1)
        while lower_bound <= upper_bound:
            period: Period = (
                Period.objects
                .filter_by_interval(interval=interval)
                .intersects(date=lower_bound)
                .first()
            )
            yield period
            lower_bound = period.upper_bound + diff

    def __str__(self):
        return self.period


@register_for_model(Interval)
class Intervals(BaseEnumModel):
    DAILY = Interval.Literal(
        duration='1 day',
        unit='day',
        pay_period=False,
    )

    WEEKLY = Interval.Literal(
        duration='1 week',
        unit='week',
        pay_period=False,
    )

    WEEKLY_SUN = Interval.Literal(
        duration='1 week',
        unit='week',
        pay_period=True,
    )

    MONTHLY = Interval.Literal(
        duration="1 month",
        unit='month',
        pay_period=False,
    )

    QUARTERLY = Interval.Literal(
        duration='3 month',
        unit='quarter',
        pay_period=False,
    )

    SEMIANNUAL = Interval.Literal(
        duration='6 month',
        unit='half_year',
        pay_period=False,
    )

    YEARLY = Interval.Literal(
        duration='1 year',
        unit='year',
        pay_period=False,
    )

    @classmethod
    def date_range(
            cls,
            start_date: Date = Date(1999, 1, 1),
            end_date: Date = Date(2029, 12, 31)
    ) -> Iterable[Date]:
        """
        Generates the days for the given date range
        """
        days = int((end_date - start_date).days)
        for n in range(days):
            yield start_date + timedelta(n)

    def get_first_week_day(self) -> int | None:
        """
        Returns the first day of the week as an ordinal number.
        Where Monday is represented by 1 and Sunday is represented by 7.
        """
        match self:
            case self.WEEKLY:
                return 1
            case self.WEEKLY_SUN:
                return 7
            case _:
                return None

    def get_period_name(self, lower_bound: Date, upper_bound: Date) -> str:
        """
        Get the name of the period
        """
        match self:
            case self.DAILY:
                return lower_bound.strftime("%Y/%m/%d")
            case self.WEEKLY:
                lower_bound_str = lower_bound.strftime("%m/%d")
                upper_bound_str = upper_bound.strftime("%m/%d")
                key_str = lower_bound.strftime("%Y W%W")
                return f'{key_str}: {lower_bound_str}-{upper_bound_str}'

            case self.WEEKLY_SUN:
                lower_bound_str = lower_bound.strftime("%m/%d")
                upper_bound_str = upper_bound.strftime("%m/%d")
                key_str = lower_bound.strftime("%Y WS%W")
                return f'{key_str}: {lower_bound_str}-{upper_bound_str}'

            case self.MONTHLY:
                return lower_bound.strftime("%Y %b")
            case self.QUARTERLY:
                lower_bound_str = lower_bound.strftime("%b")
                upper_bound_str = upper_bound.strftime("%b")
                key_str = f"{lower_bound.year} Q{lower_bound.month // 3 + 1}"
                return f'{key_str}: {lower_bound_str}-{upper_bound_str}'
            case self.SEMIANNUAL:
                lower_bound_str = lower_bound.strftime("%b")
                upper_bound_str = upper_bound.strftime("%b")
                key_str = f"{lower_bound.year} Q{lower_bound.month // 3 + 1}"
                return f'{key_str}: {lower_bound_str}-{upper_bound_str}'
            case self.YEARLY:
                return lower_bound.strftime("%Y")
            case _:
                lower_bound_str = lower_bound.strftime("%Y/%m/%d")
                upper_bound_str = upper_bound.strftime("%Y/%m/%d")
                return f'Range: {lower_bound_str}-{upper_bound_str}'

    def member_register(self):
        pay_period: bool = self.value.pay_period
        periods = defaultdict(set)

        for day in self.date_range():
            first_date = truncate(day, self.value.unit, self.get_first_week_day())
            periods[first_date].add(day)

        periods_to_insert = []
        for first_date, dates in periods.items():
            lower_bound = first_date
            upper_bound = max(dates)
            period_name = self.get_period_name(lower_bound, upper_bound)
            period = Period(
                interval_id=self.identifier,
                period=period_name,
                pay_period=pay_period,
                lower_bound=lower_bound,
                upper_bound=upper_bound,
            )
            periods_to_insert.append(period)

        Period.objects.bulk_create(
            periods_to_insert,
            ignore_conflicts=True,
        )

        Period.objects.filter(interval_id=self.identifier).update(pay_period=pay_period)


__all__ = ['Interval', 'Intervals']
