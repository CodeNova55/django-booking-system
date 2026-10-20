from django.urls import path

from bookings import views

urlpatterns = [
    path("", views.calendar, name="calendar"),
    path("book/", views.book, name="book"),
    path("confirmation/<int:pk>/", views.confirmation, name="confirmation"),
    path("schedule/<int:provider_id>/<str:day>/", views.day_schedule, name="day_schedule"),
]
