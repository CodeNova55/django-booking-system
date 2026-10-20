import datetime as dt

from django.utils import timezone

# 2030-01-07 is a Monday; 2030-01-06 is a Sunday.
MONDAY = dt.date(2030, 1, 7)
SUNDAY = dt.date(2030, 1, 6)


def at(day, hour, minute=0):
    return timezone.make_aware(dt.datetime.combine(day, dt.time(hour, minute)))
