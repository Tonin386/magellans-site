from django.shortcuts import render, redirect
from showcase.forms import ContactForm
from django.core.mail import send_mail
from dashboard.models import *
from django.conf import settings
from .forms import ContactForm

def home(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            phone = form.cleaned_data['phone']
            message = form.cleaned_data['message']

            subject = 'Contact Form Submission'
            message_body = f'Name: {name}\nEmail: {email}\nPhone: {phone}\n\nMessage:\n{message}'
            sender_email = settings.EMAIL_HOST_USER
            recipient_list = [settings.EMAIL_RECEIVER]

            print(subject, message_body, sender_email, recipient_list)
    else:
        form = ContactForm()
        
    projets = Project.objects.order_by("-shoot_date")[:6]
    
    if request.user.is_authenticated:
        redirect('/membres')
        
    return render(request, 'home.html', locals())

def projects(request):
    return render(request, 'projects.html', locals())

def contact(request):
    return render(request, 'contact.html', locals())

def join_us(request):
    return render(request, 'join_us.html', locals())