from datetime import datetime


def format_date(date, from_format, to_format):
    if not date:
        return None
    return datetime.strptime(date, from_format).strftime(to_format)
