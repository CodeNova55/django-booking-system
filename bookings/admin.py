from django.contrib import admin

from bookings.models import Appointment, Provider, Service, WorkingHours

admin.site.register(Service)
admin.site.register(Provider)
admin.site.register(WorkingHours)
admin.site.register(Appointment)
