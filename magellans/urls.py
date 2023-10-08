from django.contrib.auth import views as auth_views
from django.conf.urls.static import static
from django.urls import path, include
from django.contrib import admin
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('showcase.urls')),
    path('tresorerie/', include('bank.urls')),
    path('magasin/', include('warehouse.urls')),
    path('membres/', include('members.urls')),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('login/', auth_views.LoginView.as_view(), name='login')
]