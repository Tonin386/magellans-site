from django.shortcuts import render, redirect

def home(request):
    if request.user.is_authenticated:
        redirect('/membres')
        
    return render(request, 'home.html', locals())

def home_public(request):
    return render(request, 'home_public.html', locals())

def projects(request):
    return render(request, 'projects.html', locals())

def contact(request):
    return render(request, 'contact.html', locals())

def join_us(request):
    return render(request, 'join_us.html', locals())