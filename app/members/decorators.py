from functools import wraps
from django.shortcuts import render, redirect

def staff_required(title, og_description):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.is_staff:
                request.title = title
                request.og_description = og_description
                return view_func(request, *args, **kwargs)
        
            return render(request, "403.html", {'title': title, 'og_description': og_description}, status=403)
        return wrapper
    return decorator

def login_required(title, og_description):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated:
                request.title = title
                request.og_description = og_description
                return view_func(request, *args, **kwargs)
            return render(request, "registration/login_redirect.html", {'title': title, 'og_description': og_description})
        return wrapper
    return decorator