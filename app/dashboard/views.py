from django.utils.decorators import method_decorator
from members.decorators import staff_required
from django.views.generic import DetailView
from django.shortcuts import render
from members.models import *
from .models import *

@staff_required
def dashboard_home(request):
    return render(request, "dashboard.html", locals())

@staff_required
def dashboard_members(request):
    members = Member.objects.all()
    external_users = UnregisteredMember.objects.all()

    persons = []

    for m in members:
        persons.append(m.site_person)

    for m in external_users:
        persons.append(m.ext_person)
    
    return render(request, "dashboard_members.html", locals())

@staff_required
def dashboard_projects(request):
    projects = Project.objects.all()

    members = Member.objects.all()
    external_users = UnregisteredMember.objects.all()

    site_persons = []
    ext_persons = []

    for m in members:
        site_persons.append(m.site_person)

    for m in external_users:
        ext_persons.append(m.ext_person)

    return render(request, "dashboard_projects.html", locals())

class ProjectDetailView(DetailView):
    model = Project
    template_name = "project_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        members = Member.objects.all()
        external_users = UnregisteredMember.objects.all()

        site_persons = []
        ext_persons = []

        for m in members:
            site_persons.append(m.site_person)

        for m in external_users:
            ext_persons.append(m.ext_person)

        context["site_persons"] = site_persons
        context["ext_persons"] = ext_persons
        return context