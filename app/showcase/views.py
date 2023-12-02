from django.shortcuts import render, redirect

def home(request):
    if request.user.is_authenticated:
        redirect('/membres')
        
    return render(request, 'home.html', locals())