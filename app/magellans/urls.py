from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.contrib import admin
from .views import *

urlpatterns = [
    # path("", maintenance, name="home")
    path('admin/', admin.site.urls),
    path('auth/', include("django.contrib.auth.urls")),
    path('', include('showcase.urls')),
    path('tresorerie/', include('bank.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('magasin/', include('warehouse.urls')),
    path('membres/', include('members.urls')),
    path('deconnexion/', auth_views.LogoutView.as_view(), name='logout'),
    path('connexion/', auth_views.LoginView.as_view(), name='login'),
    path('api/', include("api.urls")),
    path('<str:filename>', FileView.as_view(), name="file_view"),
]
