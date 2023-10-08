from django.conf.urls.static import static
from django.urls import path, include
from django.contrib import admin
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('showcase.urls')),
]