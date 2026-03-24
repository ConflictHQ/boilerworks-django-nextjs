from datetime import timedelta

__all__ = [
    'truncate',
    'truncate_second',
    'truncate_minute',
    'truncate_hour',
    'truncate_day',
    'truncate_week',
    'truncate_month',
    'truncate_quarter',
    'truncate_half_year',
    'truncate_year',
]

PERIODS = {
    'second': dict(),
    'minute': dict(),
    'hour': dict(),
    'day': dict(),
    'month': dict(day=1),
    'year': dict(day=1, month=1),
}
ODD_PERIODS = ['week', 'quarter', 'half_year']


def truncate_second(datetime):
    ''' Sugar for :py:func:`truncate(datetime, 'second')` '''
    return truncate(datetime, 'second')


def truncate_minute(datetime):
    ''' Sugar for :py:func:`truncate(datetime, 'minute')` '''
    return truncate(datetime, 'minute')


def truncate_hour(datetime):
    ''' Sugar for :py:func:`truncate(datetime, 'hour')` '''
    return truncate(datetime, 'hour')


def truncate_day(datetime):
    ''' Sugar for :py:func:`truncate(datetime, 'day')` '''
    return truncate(datetime, 'day')


def truncate_week(datetime, week_start=7):
    '''
    Truncates a date to the first day of an ISO 8601 week, i.e. monday.

    :params datetime: an initialized datetime object
    :params week_start: The first day of a week as an ordinal number. Starts Monday 1 ends Sunday 7. Defaults to Sunday.
    :return: `datetime` with the original day set to monday
    :rtype: :py:mod:`datetime` datetime object
    '''
    days_delta = (
        7 - abs(week_start - datetime.isoweekday())
        if week_start > datetime.isoweekday()
        else datetime.isoweekday() - week_start
    )
    datetime = truncate(datetime, 'day')
    return datetime - timedelta(days=days_delta)


def truncate_month(datetime):
    ''' Sugar for :py:func:`truncate(datetime, 'month')` '''
    return truncate(datetime, 'month')


def truncate_quarter(datetime):
    '''
    Truncates the datetime to the first day of the quarter for this date.

    :params datetime: an initialized datetime object
    :return: `datetime` with the month set to the first month of this quarter
    :rtype: :py:mod:`datetime` datetime object
    '''
    datetime = truncate(datetime, 'month')

    month = datetime.month
    if 1 <= month <= 3:
        return datetime.replace(month=1)
    elif 4 <= month <= 6:
        return datetime.replace(month=4)
    elif 7 <= month <= 9:
        return datetime.replace(month=7)
    elif 10 <= month <= 12:
        return datetime.replace(month=10)


def truncate_half_year(datetime):
    '''
    Truncates the datetime to the first day of the half year for this date.

    :params datetime: an initialized datetime object
    :return: `datetime` with the month set to the first month of this half year
    :rtype: :py:mod:`datetime` datetime object
    '''
    datetime = truncate(datetime, 'month')

    month = datetime.month

    if 1 <= month <= 6:
        return datetime.replace(month=1)
    elif 7 <= month <= 12:
        return datetime.replace(month=7)


def truncate_year(datetime):
    ''' Sugar for :py:func:`truncate(datetime, 'year')` '''
    return truncate(datetime, 'year')


def truncate(datetime, truncate_to='day', week_start: int = 7):
    '''
    Truncates a datetime to have the values with higher precision than
    the one set as `truncate_to` as zero (or one for day and month).

    Possible values for `truncate_to`:

    * second
    * minute
    * hour
    * day
    * week (iso week i.e. to monday)
    * month
    * quarter
    * half_year
    * year

    Examples::

       >>> truncate(datetime(2012, 12, 12, 12), 'day')
       datetime(2012, 12, 12)
       >>> truncate(datetime(2012, 12, 14, 12, 15), 'quarter')
       datetime(2012, 10, 1)
       >>> truncate(datetime(2012, 3, 1), 'week', 1)
       datetime(2012, 2, 27)

    :params datetime: an initialized datetime object
    :params truncate_to: The highest precision to keep its original data.
    :params week_start: The first day of a week as an ordinal number. Starts Monday 1 ends Sunday 7. Defaults to Sunday.
    :return: datetime with `truncated_to` as the highest level of precision
    :rtype: :py:mod:`datetime` datetime object
    '''
    if truncate_to in PERIODS:
        return datetime.replace(**PERIODS[truncate_to])
    elif truncate_to in ODD_PERIODS:
        if truncate_to == 'week':
            return truncate_week(datetime, week_start)
        elif truncate_to == 'quarter':
            return truncate_quarter(datetime)
        elif truncate_to == 'half_year':
            return truncate_half_year(datetime)
    else:
        raise ValueError('truncate_to not valid. Valid periods: {}'.format(
            ', '.join(list(PERIODS.keys()) + list(ODD_PERIODS))
        ))
