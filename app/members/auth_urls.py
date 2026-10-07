from django.urls import path
from django.views.generic import RedirectView

from . import auth_views

urlpatterns = [
    path("connexion/", auth_views.LoginView.as_view(), name="login"),
    path("deconnexion/", auth_views.LogoutView.as_view(), name="logout"),
    path("inscription/", auth_views.register, name="register"),
    path("inscription/merci/", auth_views.register_done, name="register-done"),
    path("inscription/renvoyer-le-lien/", auth_views.resend_activation, name="resend-activation"),
    path("membres/activate/<str:uidb64>/<str:token>/", auth_views.activate, name="activate"),
    path("bienvenue/<str:uidb64>/<str:token>/", auth_views.InvitationView.as_view(), name="invitation"),
    path("mot-de-passe/oublie/", auth_views.PasswordResetView.as_view(), name="password_reset"),
    path("mot-de-passe/oublie/envoye/", auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path(
        "mot-de-passe/nouveau/<str:uidb64>/<str:token>/",
        auth_views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    # Anciennes adresses
    path("membres/inscription/", RedirectView.as_view(pattern_name="register", permanent=True)),
    path("auth/login/", RedirectView.as_view(pattern_name="login", permanent=True)),
    path("auth/password_reset/", RedirectView.as_view(pattern_name="password_reset", permanent=True)),
    path("auth/reset/<str:uidb64>/<str:token>/", RedirectView.as_view(pattern_name="password_reset_confirm", permanent=True)),
]
