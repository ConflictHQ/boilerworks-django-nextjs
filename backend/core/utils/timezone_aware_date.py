from datetime import datetime

import django_filters
import pytz
from django.conf import settings
from django_filters.fields import DateRangeField
from django_filters.widgets import DateRangeWidget


class TimezoneAwareDateRangeWidget(DateRangeWidget):

    def value_from_datadict(self, data, files, name):
        value = data.get(name)
        if value is None:
            return None
        return [value[0], value[1]]


class TimezoneAwareDateRangeField(DateRangeField):
    widget = TimezoneAwareDateRangeWidget


class TimezoneAwareDateMixin:
    @classmethod
    def _replace_date_with_date(cls, date_to_replace):
        date_now = datetime.now()
        return datetime(date_to_replace.year, date_to_replace.month, date_to_replace.day, date_now.hour,
                        date_now.minute, date_now.second).astimezone(pytz.timezone(settings.COMPANY_TIME_ZONE))


class TimezoneAwareDateRangeFilter(django_filters.DateFromToRangeFilter, TimezoneAwareDateMixin):
    field_class = TimezoneAwareDateRangeField

    def filter(self, qs, value):
        if not value:
            return qs

        lower_bound, upper_bound = value.start, value.stop

        lower_bound_localized = self._replace_date_with_date(lower_bound)
        upper_bound_localized = self._replace_date_with_date(upper_bound)

        lower_bound = lower_bound_localized.date()
        upper_bound = upper_bound_localized.date()

        value = slice(lower_bound, upper_bound, value.step)
        return super().filter(qs, value)


class TimezoneAwareDateFilter(django_filters.DateFilter, TimezoneAwareDateMixin):
    def filter(self, qs, value):
        if not value:
            return qs
        bound_localized = self._replace_date_with_date(value)
        bound = bound_localized.date()
        return super().filter(qs, bound)
