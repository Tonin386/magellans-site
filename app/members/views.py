from django.contrib.auth.decorators import login_required
from django.views.generic import DetailView
from django.shortcuts import render
from .models import Member

def members(request):
    return "Hello"

@login_required
def my_profile(request):
    return render(request, 'member_detail.html', {'object': request.user})

class MemberDetailView(DetailView):
    model = Member
    template_name="member_detail.html"
    