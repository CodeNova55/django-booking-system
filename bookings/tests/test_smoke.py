def test_bookings_app_installed(settings):
    assert "bookings" in settings.INSTALLED_APPS
