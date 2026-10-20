import datetime as dt

import pytest
from urllib.parse import urlencode
from django.urls import reverse

from bookings.models import Appointment
from bookings.tests.helpers import MONDAY, at


def slot_url(provider, service, start):
    return reverse("book") + (
        f"?provider={provider.pk}&service={service.pk}&{urlencode({'start': start.isoformat()})}"
    )


def test_calendar_renders_free_slots(client, provider, service):
    resp = client.get(reverse("calendar"), {
        "provider": provider.pk, "service": service.pk,
        "week": MONDAY.isoformat(),
    })
    assert resp.status_code == 200
    assert "09:00" in resp.content.decode()


def test_calendar_with_no_providers(client, db):
    resp = client.get(reverse("calendar"))
    assert resp.status_code == 200
    assert "No providers yet" in resp.content.decode()


def test_book_form_renders(client, provider, service):
    resp = client.get(slot_url(provider, service, at(MONDAY, 9)))
    assert resp.status_code == 200
    assert "Confirm your booking" in resp.content.decode()


def test_booking_flow_creates_appointment(client, provider, service):
    resp = client.post(reverse("book"), {
        "provider": provider.pk, "service": service.pk,
        "start": at(MONDAY, 9).isoformat(),
        "customer_name": "Alice", "customer_email": "alice@example.com",
    })
    assert resp.status_code == 302
    appt = Appointment.objects.get()
    assert appt.customer_name == "Alice"
    assert resp.url == reverse("confirmation", args=[appt.pk])


def test_double_booking_via_view_shows_error(client, provider, service):
    data = {
        "provider": provider.pk, "service": service.pk,
        "start": at(MONDAY, 9).isoformat(),
        "customer_name": "Alice", "customer_email": "alice@example.com",
    }
    client.post(reverse("book"), data)
    resp = client.post(reverse("book"), data, follow=True)
    assert Appointment.objects.count() == 1
    assert "not available" in resp.content.decode()


def test_invalid_form_does_not_book(client, provider, service):
    resp = client.post(reverse("book"), {
        "provider": provider.pk, "service": service.pk,
        "start": at(MONDAY, 9).isoformat(),
        "customer_name": "", "customer_email": "not-an-email",
    })
    assert resp.status_code == 200
    assert Appointment.objects.count() == 0


def test_day_schedule_lists_appointments(client, provider, service):
    Appointment.objects.create(
        provider=provider, service=service, customer_name="Zed",
        customer_email="z@example.com", start=at(MONDAY, 10),
        end=at(MONDAY, 10, 30),
    )
    resp = client.get(reverse("day_schedule", args=[provider.pk, MONDAY.isoformat()]))
    assert "Zed" in resp.content.decode()

