import datetime as dt

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from bookings.models import Appointment, WorkingHours
from bookings.tests.helpers import MONDAY, at


def test_working_hours_end_must_be_after_start(provider):
    hours = WorkingHours(
        provider=provider, weekday=0,
        start_time=dt.time(12), end_time=dt.time(9),
    )
    with pytest.raises(ValidationError):
        hours.clean()


def test_database_blocks_duplicate_confirmed_slot(provider, service):
    start = at(MONDAY, 9)
    kwargs = dict(
        provider=provider, service=service, customer_name="A",
        customer_email="a@example.com", start=start,
        end=start + dt.timedelta(minutes=30),
    )
    Appointment.objects.create(**kwargs)
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Appointment.objects.create(**kwargs)
