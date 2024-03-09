from django.contrib.auth.decorators import login_required
from django.shortcuts import render, HttpResponse
from django.views.generic import DetailView
from .models import Member

@login_required
def members(request):
    return render(request, "members.html", locals())

@login_required
def my_profile(request):
    return render(request, 'member_detail.html', {'object': request.user})

class MemberDetailView(DetailView):
    model = Member
    template_name="member_detail.html"