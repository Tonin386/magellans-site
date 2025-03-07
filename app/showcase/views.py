from django.shortcuts import render, HttpResponse
from django.utils.safestring import mark_safe
from showcase.forms import ContactForm
from django.core.mail import send_mail
from django.conf import settings
from .forms import ContactForm
from dashboard.models import *

def home(request):
    title = "Associations Magellans - Site officiel"
    og_description = "Site officiel de l'association d'audiovisuel Magellans"
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            phone = form.cleaned_data['phone']
            message = form.cleaned_data['message']

            subject = f'Nouveau formulaire reçu de {email}'

            message_body = mark_safe(f'{message}\n\n--------------------\n{name}\n{email}\n{phone}')
            recipient_list = [settings.EMAIL_RECEIVER, 'magellans.pro@gmail.com', 'magellans.contact@gmail.com', email]
            
            send_mail(subject, message_body, settings.DEFAULT_FROM_EMAIL, recipient_list)
    else:
        form = ContactForm()
        
    projets = Project.objects.filter(public=True).order_by("-release_date")[:6]
        
    return render(request, 'home.html', locals())

def projects(request):
    title = "Projets"
    og_description = "Projets auxquels l'association Magellans a participé."
    projets = Project.objects.filter(public=True).order_by('-release_date')
    return render(request, 'projects.html', locals())