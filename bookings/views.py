import datetime as dt

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from bookings.availability import get_available_slots
from bookings.booking import BookingError, book_appointment
from bookings.forms import BookingForm, monday_of
from bookings.models import Appointment, Provider, Service


def _parse_date(value, default):
    try:
        return dt.date.fromisoformat(value)
    except (TypeError, ValueError):
        return default


def calendar(request):
    providers = Provider.objects.prefetch_related("services")
    provider = None
    service = None
    if request.GET.get("provider"):
        provider = providers.filter(pk=request.GET["provider"]).first()
    if provider is None:
        provider = providers.first()

    if provider is not None:
        services = provider.services.all()
        if request.GET.get("service"):
            service = services.filter(pk=request.GET["service"]).first()
        if service is None:
            service = services.first()
    else:
        services = Service.objects.none()

    today = timezone.localdate()
    week_start = monday_of(_parse_date(request.GET.get("week"), today))

    days = []
    if provider and service:
        for i in range(7):
            day = week_start + dt.timedelta(days=i)
            slots = get_available_slots(provider, service, day)
            days.append({"date": day, "slots": slots, "is_today": day == today})

    context = {
        "providers": providers,
        "services": services,
        "provider": provider,
        "service": service,
        "days": days,
        "week_start": week_start,
        "prev_week": week_start - dt.timedelta(days=7),
        "next_week": week_start + dt.timedelta(days=7),
    }
    return render(request, "bookings/calendar.html", context)


def book(request):
    """Booking form. The slot is passed as ?provider=&service=&start=ISO."""
    data = request.POST if request.method == "POST" else request.GET
    provider = get_object_or_404(Provider, pk=data.get("provider"))
    service = get_object_or_404(Service, pk=data.get("service"))
    try:
        start = dt.datetime.fromisoformat(data.get("start", ""))
    except ValueError:
        messages.error(request, "Invalid time slot.")
        return redirect("calendar")
    if timezone.is_naive(start):
        start = timezone.make_aware(start)

    if request.method == "POST":
        form = BookingForm(request.POST)
        if form.is_valid():
            try:
                appt = book_appointment(
                    provider=provider, service=service, start=start,
                    customer_name=form.cleaned_data["customer_name"],
                    customer_email=form.cleaned_data["customer_email"],
                )
            except BookingError as exc:
                messages.error(request, str(exc))
                return redirect(
                    f"/?provider={provider.pk}&service={service.pk}"
                    f"&week={timezone.localtime(start).date().isoformat()}"
                )
            return redirect("confirmation", pk=appt.pk)
    else:
        form = BookingForm()

    return render(request, "bookings/book.html", {
        "form": form, "provider": provider, "service": service, "start": start,
    })


def confirmation(request, pk):
    appt = get_object_or_404(Appointment, pk=pk)
    return render(request, "bookings/confirmation.html", {"appt": appt})


def day_schedule(request, provider_id, day):
    provider = get_object_or_404(Provider, pk=provider_id)
    the_day = _parse_date(day, timezone.localdate())
    start = timezone.make_aware(dt.datetime.combine(the_day, dt.time.min))
    appts = Appointment.objects.filter(
        provider=provider, status=Appointment.Status.CONFIRMED,
        start__gte=start, start__lt=start + dt.timedelta(days=1),
    ).select_related("service")
    return render(request, "bookings/day.html", {
        "provider": provider, "day": the_day, "appointments": appts,
    })
