import datetime as dt

from django import forms

from bookings.models import Provider, Service


class BookingForm(forms.Form):
    customer_name = forms.CharField(max_length=100)
    customer_email = forms.EmailField()


class CalendarFilterForm(forms.Form):
    provider = forms.ModelChoiceField(queryset=Provider.objects.all())
    service = forms.ModelChoiceField(queryset=Service.objects.all())
    week = forms.DateField(required=False)


def monday_of(day):
    return day - dt.timedelta(days=day.weekday())
