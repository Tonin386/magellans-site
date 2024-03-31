from functools import wraps
from django.shortcuts import render


def staff_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_staff:
            return view_func(request, *args, **kwargs)
        
        return render(request, "403.html", status=403)
    return wrapper