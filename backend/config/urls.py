
from django.urls import include
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/accounts/", include("apps.accounts.urls")), #apps/accounts/urls.py
    # path("api/auth/", include("apps.accounts.urls")),
]
