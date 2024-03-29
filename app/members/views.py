from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.shortcuts import render, HttpResponse
from django.utils.encoding import force_bytes
from django.views.generic import DetailView
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.contrib import messages
from django.conf import settings
from .forms import RegisterForm
from .models import Member
from .forms import *
import secrets
import string


@login_required
def members(request):
    return render(request, "members.html", locals())

@login_required
def my_profile(request):
    form = EditProfileForm()
    if request.method == "POST":
        form = EditProfileForm(request.POST)
        if form.is_valid():
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data['last_name']
            request.user.phone = form.cleaned_data['phone']
            request.user.gender = form.cleaned_data['gender']
            request.user.save()
            
    return render(request, 'member_detail.html', {'object': request.user, 'form': form})

def register(request):
    form = RegisterForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            new_user = form.save()
            new_user.is_active = False
            
            token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(128))
            new_user.api_token = token
            
            new_user.save()
            
            token = default_token_generator.make_token(new_user)
            uidb64 = urlsafe_base64_encode(force_bytes(new_user.pk))
            activation_url = "https://magellans.fr/membres/activate/{}/{}".format(uidb64, token)
            
            subject = "Activation de votre compte magellans.fr"
            message = render_to_string('registration/activation_email.html', {'user': new_user, 'activation_url': activation_url})
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [new_user.email])

            messages.success(request, 'Vous avez reçu un email pour activer votre compte.')
            
    return render(request, "registration/register.html", locals())

def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Member.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Member.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        # Activate user account
        user.is_active = True
        user.save()
        # Redirect to success page or login page
        return redirect('activation_done')
    
    return redirect('activation_failed')

def activation_done(request):
    return render(request, 'registration/activation_done.html', locals())

def activation_failed(request):
    return render(request, 'registration/activation_failed.html', locals())

class MemberDetailView(DetailView):
    model = Member
    template_name="member_detail.html"