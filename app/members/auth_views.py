"""Connexion, inscription, activation et mots de passe."""

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.contrib.auth.tokens import default_token_generator
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.http import require_http_methods

from core.antispam import rate_limited
from core.audit import log_activity
from core.emails import send_templated_email

from .forms import LoginForm, RegisterForm, StyledPasswordResetForm, StyledSetPasswordForm
from .models import Member, Person


def activation_path(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return reverse("activate", kwargs={"uidb64": uid, "token": token})


def invitation_path(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return reverse("invitation", kwargs={"uidb64": uid, "token": token})


def send_activation_email(user):
    return send_templated_email("account_activation", {"user": user, "activation_path": activation_path(user)}, [user.email])


def send_invitation_email(user, membership=None):
    return send_templated_email(
        "account_invitation",
        {"user": user, "invitation_path": invitation_path(user), "membership": membership},
        [user.email],
    )


class LoginView(auth_views.LoginView):
    form_class = LoginForm
    template_name = "auth/login.html"
    redirect_authenticated_user = True

    def post(self, request, *args, **kwargs):
        if rate_limited(request, "login", limit=10, period=15 * 60):
            messages.error(request, "Trop de tentatives de connexion. Patiente quelques minutes avant de réessayer.")
            return redirect("login")
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Bon retour parmi nous, {self.request.user.get_short_name()} !")
        return response


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy("home")

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.info(request, "Tu es déconnecté·e. À bientôt !")
        return response


@require_http_methods(["GET", "POST"])
def register(request):
    if request.user.is_authenticated:
        return redirect("members:home")
    form = RegisterForm(request.POST or None)
    if request.method == "POST":
        if rate_limited(request, "register", limit=5, period=3600):
            form.add_error(None, "Trop d'inscriptions depuis ta connexion. Réessaie plus tard.")
        elif form.is_valid():
            data = form.cleaned_data
            existing = Member.objects.filter(email__iexact=data["email"]).first()
            if existing and existing.is_active:
                form.add_error(
                    "email",
                    "Un compte existe déjà avec cette adresse. Tu peux te connecter ou réinitialiser ton mot de passe.",
                )
            elif existing:
                # Compte créé mais jamais activé (inscription inachevée ou adhésion HelloAsso) : on renvoie le lien.
                if existing.has_usable_password():
                    send_activation_email(existing)
                else:
                    send_invitation_email(existing)
                return redirect("register-done")
            else:
                with transaction.atomic():
                    person = Person(
                        first_name=data["first_name"].strip(),
                        last_name=data["last_name"].strip(),
                        email=data["email"],
                        phone=data["phone"],
                        role="E",
                    )
                    user = Member.objects.create_user(
                        data["email"], data["password1"], is_active=False, person=person
                    )
                send_activation_email(user)
                log_activity(request, "register", f"Nouvelle inscription : {person.full_name} ({user.email}).", target=person, category="account")
                return redirect("register-done")
    return render(request, "auth/register.html", {"form": form})


def register_done(request):
    return render(request, "auth/register_done.html")


def _user_from_uid(uidb64):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        return Member.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Member.DoesNotExist):
        return None


def activate(request, uidb64, token):
    user = _user_from_uid(uidb64)
    if user is None:
        return render(request, "auth/activation_failed.html", status=400)
    if user.is_active and user.has_usable_password():
        messages.info(request, "Ton compte est déjà activé : tu peux te connecter.")
        return redirect("login")
    if not default_token_generator.check_token(user, token):
        return render(request, "auth/activation_failed.html", {"user_email": user.email}, status=400)
    if not user.has_usable_password():
        # Compte créé lors d'une adhésion : il faut d'abord choisir un mot de passe.
        return redirect("invitation", uidb64=uidb64, token=token)
    user.is_active = True
    user.save(update_fields=["is_active"])
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    log_activity(request, "activate", f"Compte activé : {user}.", target=user.person, category="account")
    messages.success(request, "Ton compte est activé, bienvenue sur le site de Magellans !")
    return redirect("members:home")


@require_http_methods(["POST"])
def resend_activation(request):
    email = (request.POST.get("email") or "").strip()
    if email and not rate_limited(request, "resend-activation", limit=3, period=3600):
        user = Member.objects.filter(email__iexact=email, is_active=False).first()
        if user:
            if user.has_usable_password():
                send_activation_email(user)
            else:
                send_invitation_email(user)
    messages.info(request, "Si un compte non activé correspond à cette adresse, un nouveau lien vient d'être envoyé.")
    return redirect("login")


class PasswordResetView(auth_views.PasswordResetView):
    form_class = StyledPasswordResetForm
    template_name = "auth/password_reset.html"
    success_url = reverse_lazy("password_reset_done")

    def post(self, request, *args, **kwargs):
        if rate_limited(request, "password-reset", limit=5, period=3600):
            messages.error(request, "Trop de demandes. Réessaie dans une heure.")
            return redirect("password_reset")
        return super().post(request, *args, **kwargs)


class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = "auth/password_reset_done.html"


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    form_class = StyledSetPasswordForm
    template_name = "auth/password_reset_confirm.html"
    success_url = reverse_lazy("login")
    post_reset_login = False

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.user
        if not user.is_active:
            user.is_active = True
            user.save(update_fields=["is_active"])
        messages.success(self.request, "Ton mot de passe est enregistré : tu peux te connecter.")
        return response


class InvitationView(PasswordResetConfirmView):
    """Premier accès d'un·e adhérent·e dont le compte a été créé automatiquement."""

    template_name = "auth/invitation.html"
    success_url = reverse_lazy("members:home")
    post_reset_login = True
    post_reset_login_backend = "django.contrib.auth.backends.ModelBackend"

    def form_valid(self, form):
        user = form.user
        user.is_active = True
        user.save(update_fields=["is_active"])
        response = super(PasswordResetConfirmView, self).form_valid(form)
        log_activity(self.request, "activate", f"Premier accès d'un·e adhérent·e : {user}.", target=user.person, category="account")
        messages.success(self.request, "Bienvenue à bord ! Ton espace membre est prêt.")
        return response
