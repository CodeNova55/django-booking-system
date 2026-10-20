from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class Service(models.Model):
    name = models.CharField(max_length=100)
    duration_minutes = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.name} ({self.duration_minutes} min)"


class Provider(models.Model):
    """A stylist, doctor, or anyone who takes appointments."""

    name = models.CharField(max_length=100)
    services = models.ManyToManyField(Service, related_name="providers")

    def __str__(self):
        return self.name


class WorkingHours(models.Model):
    WEEKDAYS = [
        (0, "Monday"), (1, "Tuesday"), (2, "Wednesday"), (3, "Thursday"),
        (4, "Friday"), (5, "Saturday"), (6, "Sunday"),
    ]

    provider = models.ForeignKey(
        Provider, on_delete=models.CASCADE, related_name="working_hours"
    )
    weekday = models.PositiveSmallIntegerField(choices=WEEKDAYS)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ["provider", "weekday", "start_time"]

    def clean(self):
        if self.end_time <= self.start_time:
            raise ValidationError("End time must be after start time.")

    def __str__(self):
        return f"{self.provider} {self.get_weekday_display()} {self.start_time}-{self.end_time}"


class Appointment(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"

    provider = models.ForeignKey(
        Provider, on_delete=models.CASCADE, related_name="appointments"
    )
    service = models.ForeignKey(Service, on_delete=models.PROTECT)
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    start = models.DateTimeField()
    end = models.DateTimeField()
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.CONFIRMED
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start"]
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "start"],
                condition=Q(status="confirmed"),
                name="unique_confirmed_slot_per_provider",
            )
        ]

    def __str__(self):
        return f"{self.customer_name} with {self.provider} at {self.start:%Y-%m-%d %H:%M}"
