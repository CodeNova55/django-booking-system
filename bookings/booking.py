from datetime import timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone

from bookings.availability import get_available_slots
from bookings.models import Appointment, Provider


class BookingError(Exception):
    """Base class for booking problems."""


class SlotUnavailable(BookingError):
    """The requested time is not free (or not a valid slot)."""


def book_appointment(*, provider, service, customer_name, customer_email,
                     start, now=None):
    if not provider.services.filter(pk=service.pk).exists():
        raise BookingError("This provider does not offer that service.")

    day = timezone.localtime(start).date()
    try:
        with transaction.atomic():
            # Lock the provider row so concurrent bookings queue up
            # (a no-op on SQLite, effective on PostgreSQL/MySQL).
            Provider.objects.select_for_update().get(pk=provider.pk)

            if start not in get_available_slots(provider, service, day, now=now):
                raise SlotUnavailable("That time slot is not available.")

            return Appointment.objects.create(
                provider=provider,
                service=service,
                customer_name=customer_name,
                customer_email=customer_email,
                start=start,
                end=start + timedelta(minutes=service.duration_minutes),
            )
    except IntegrityError:
        # The database constraint caught a race the check above missed.
        raise SlotUnavailable("That time slot was just taken.")


def cancel_appointment(appointment):
    appointment.status = Appointment.Status.CANCELLED
    appointment.save(update_fields=["status"])
    return appointment
