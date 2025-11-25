from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    # Підключаємо 'activities/urls.py'
    path("api/", include("activities.urls")),

    # Підключаємо URL-и для кнопки "Log in" у DRF
    path('api-auth/', include('rest_framework.urls')),
]