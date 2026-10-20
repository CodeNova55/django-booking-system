import datetime as dt

from bookings.availability import get_available_slots
from bookings.models import Appointment
from bookings.tests.helpers import MONDAY, SUNDAY, at


def make_appointment(provider, service, start, status="confirmed"):
    return Appointment.objects.create(
        provider=provider, service=service, customer_name="Test",
        customer_email="t@example.com", start=start,
        end=start + dt.timedelta(minutes=service.duration_minutes),
        status=status,
    )


def test_full_day_of_slots(provider, service):
    slots = get_available_slots(provider, service, MONDAY)
    assert len(slots) == 6
    assert slots[0] == at(MONDAY, 9)
    assert slots[-1] == at(MONDAY, 11, 30)


def test_no_slots_on_day_off(provider, service):
    assert get_available_slots(provider, service, SUNDAY) == []


def test_booked_slot_is_removed(provider, service):
    make_appointment(provider, service, at(MONDAY, 10))
    slots = get_available_slots(provider, service, MONDAY)
    assert at(MONDAY, 10) not in slots
    assert len(slots) == 5


def test_longer_service_cannot_overlap_a_booking(provider, service, long_service):
    make_appointment(provider, service, at(MONDAY, 9, 30))  # 09:30-10:00
    slots = get_available_slots(provider, long_service, MONDAY)
    assert at(MONDAY, 9) not in slots      # 09:00-10:00 overlaps
    assert at(MONDAY, 9, 30) not in slots  # 09:30-10:30 overlaps
    assert at(MONDAY, 10) in slots         # 10:00-11:00 is free


def test_service_too_long_for_window(provider):
    from bookings.models import Service

    marathon = Service.objects.create(name="Marathon", duration_minutes=240)
    provider.services.add(marathon)
    assert get_available_slots(provider, marathon, MONDAY) == []


def test_past_slots_are_excluded(provider, service):
    slots = get_available_slots(provider, service, MONDAY, now=at(MONDAY, 10))
    assert slots == [at(MONDAY, 10, 30), at(MONDAY, 11), at(MONDAY, 11, 30)]


def test_cancelled_appointment_does_not_block(provider, service):
    make_appointment(provider, service, at(MONDAY, 10), status="cancelled")
    assert at(MONDAY, 10) in get_available_slots(provider, service, MONDAY)
