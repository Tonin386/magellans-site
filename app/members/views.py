from django.contrib.auth.decorators import login_required
from django.shortcuts import render, HttpResponse
from django.views.generic import DetailView
from .models import Member
from .forms import *

from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib import messages
from django.conf import settings

@login_required
def members(request):
    return render(request, "members.html", locals())

@login_required
def my_profile(request):
    return render(request, 'member_detail.html', {'object': request.user})

def forgot_password(request):
    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = Member.objects.get(email=email)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                reset_link = 'https://magellans.fr/auth/reset_password/{}/{}/'.format(uid, token)

                email_subject = 'Réinitialisation mot de passe magellans.fr'
                email_body = render_to_string('registration/reset_password_email.html', {
                    'reset_link': reset_link,
                })
                send_mail(email_subject, '', settings.EMAIL_HOST_USER, [email], html_message=email_body)

                messages.success(request, 'Vous avez reçu un lien de réinitialisation de mot de passe.')
            except Member.DoesNotExist:
                messages.error(request, 'Cet email n\'existe pas.')
    else:
        form = ForgotPasswordForm()
        
    return render(request, 'reset_password.html', locals())

class MemberDetailView(DetailView):
    model = Member
    template_name="member_detail.html"