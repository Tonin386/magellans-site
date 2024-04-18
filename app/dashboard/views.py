from django.utils.decorators import method_decorator
from members.decorators import staff_required
from django.views.generic import DetailView
from django.shortcuts import render
from warehouse.models import *
from members.models import *
from .models import *

@staff_required("Tableau de bord de Magellans", "Page du dashboard pour l'administration de l'association Magellans.")
def dashboard_home(request):
    title = request.title
    og_description = request.og_description
    return render(request, "dashboard.html", locals())

@staff_required("Tableau de bord utilisateurs", "Page de gestion des membres de l'association Magellans.")
def dashboard_members(request):
    title = request.title
    og_description = request.og_description
    members = Member.objects.all()
    external_users = UnregisteredMember.objects.all()
    
    return render(request, "dashboard_members.html", locals())

@staff_required("Tableau de bord projets", "Page de gestion des projets de l'association Magellans.")
def dashboard_projects(request):
    title = request.title
    og_description = request.og_description

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

@staff_required("Tableau de bord commandes", "Page de gestion des réservations et commande du magasin de l'association Magellans.")
def dashboard_orders(request):
    title = request.title
    og_description = request.og_description

    orders = Order.objects.all()

    return render(request, "dashboard_orders.html", locals())

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
        context["title"] = f"Projet {self.object.name}"
        context["og_description"] = f"Page des détails du projet '{self.object.name}' auquel a participé l'association Magellans."
        return context