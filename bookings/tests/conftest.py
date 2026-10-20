import datetime as dt

import pytest

from bookings.models import Provider, Service, WorkingHours


@pytest.fixture
def service(db):
    return Service.objects.create(name="Haircut", duration_minutes=30)


@pytest.fixture
def long_service(db):
    return Service.objects.create(name="Colouring", duration_minutes=60)


@pytest.fixture
def provider(db, service, long_service):
    p = Provider.objects.create(name="Amina")
    p.services.add(service, long_service)
    for weekday in range(5):  # Monday to Friday, 09:00-12:00
        WorkingHours.objects.create(
            provider=p, weekday=weekday,
            start_time=dt.time(9), end_time=dt.time(12),
        )
    return p
