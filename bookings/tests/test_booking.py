import pytest

from bookings.booking import (
    BookingError,
    SlotUnavailable,
    book_appointment,
    cancel_appointment,
)
from bookings.models import Provider, Service
from bookings.tests.helpers import MONDAY, at


def book(provider, service, start, name="Alice"):
    return book_appointment(
        provider=provider, service=service, customer_name=name,
        customer_email="a@example.com", start=start,
    )


def test_book_creates_confirmed_appointment(provider, service):
    appt = book(provider, service, at(MONDAY, 9))
    assert appt.status == "confirmed"
    assert appt.end == at(MONDAY, 9, 30)


def test_double_booking_same_slot_is_rejected(provider, service):
    book(provider, service, at(MONDAY, 9))
    with pytest.raises(SlotUnavailable):
        book(provider, service, at(MONDAY, 9), name="Bob")


def test_overlapping_booking_is_rejected(provider, service, long_service):
    book(provider, service, at(MONDAY, 9, 30))
    with pytest.raises(SlotUnavailable):
        book(provider, long_service, at(MONDAY, 9))


def test_outside_working_hours_is_rejected(provider, service):
    with pytest.raises(SlotUnavailable):
        book(provider, service, at(MONDAY, 13))


def test_off_grid_time_is_rejected(provider, service):
    with pytest.raises(SlotUnavailable):
        book(provider, service, at(MONDAY, 9, 10))


def test_provider_must_offer_service(provider):
    other = Service.objects.create(name="Massage", duration_minutes=30)
    with pytest.raises(BookingError):
        book(provider, other, at(MONDAY, 9))


def test_cancel_frees_the_slot(provider, service):
    appt = book(provider, service, at(MONDAY, 9))
    cancel_appointment(appt)
    again = book(provider, service, at(MONDAY, 9), name="Bob")
    assert again.pk != appt.pk


def test_different_providers_can_share_a_time(provider, service):
    other = Provider.objects.create(name="Brian")
    other.services.add(service)
    other.working_hours.create(
        weekday=0, start_time=provider.working_hours.first().start_time,
        end_time=provider.working_hours.first().end_time,
    )
    book(provider, service, at(MONDAY, 9))
    assert book(other, service, at(MONDAY, 9)).provider == other
