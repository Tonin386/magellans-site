from django.urls import path

from . import views

app_name = "funding"

urlpatterns = [
    path("", views.funding_list, name="list"),
    path("nouvelle/", views.funding_create, name="create"),
    path("<int:pk>/", views.funding_detail, name="detail"),
    path("<int:pk>/message/", views.funding_message, name="message"),
]
