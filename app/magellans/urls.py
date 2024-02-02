from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.contrib import admin

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('showcase.urls')),
    path('tresorerie/', include('bank.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('magasin/', include('warehouse.urls')),
    path('membres/', include('members.urls')),
    path('deconnexion/', auth_views.LogoutView.as_view(), name='logout'),
    path('connexion/', auth_views.LoginView.as_view(), name='login')
]