from datetime import datetime, time, timedelta

from django.utils import timezone

from bookings.models import Appointment


def _aware(day, t):
    return timezone.make_aware(datetime.combine(day, t))


def get_available_slots(provider, service, day, step_minutes=30, now=None):
    """Return the start times (aware datetimes) a customer can book on `day`.

    A slot is available if the whole service fits inside a working-hours window,
    it starts in the future, and it does not overlap a confirmed appointment.
    """
    now = now or timezone.now()
    duration = timedelta(minutes=service.duration_minutes)
    step = timedelta(minutes=step_minutes)

    day_start = _aware(day, time.min)
    day_end = day_start + timedelta(days=1)
    busy = list(
        Appointment.objects.filter(
            provider=provider,
            status=Appointment.Status.CONFIRMED,
            start__lt=day_end,
            end__gt=day_start,
        ).values_list("start", "end")
    )

    slots = []
    for window in provider.working_hours.filter(weekday=day.weekday()):
        cursor = _aware(day, window.start_time)
        window_end = _aware(day, window.end_time)
        while cursor + duration <= window_end:
            end = cursor + duration
            overlaps = any(s < end and e > cursor for s, e in busy)
            if cursor > now and not overlaps:
                slots.append(cursor)
            cursor += step
    return sorted(slots)
