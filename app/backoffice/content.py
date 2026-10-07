"""Déclaration des contenus éditables via le CRUD générique."""

from core.models import FAQEntry, Page, Service, TeamMember, TimelineEntry
from dashboard.models import ResourceFile
from memberships.models import Season
from warehouse.forms import TagForm
from warehouse.models import Tag

from .crud import Crud
from .forms import FAQEntryForm, PageForm, ResourceForm, ServiceForm, TeamMemberForm, TimelineEntryForm


class TeamCrud(Crud):
    model = TeamMember
    form_class = TeamMemberForm
    name = "team"
    title = "Équipe (CA)"
    singular = "membre de l'équipe"
    icon = "users"
    columns = [("Nom", "name"), ("Fonction", "role_title"), ("Saison", "season"), ("Visible", "is_visible")]
    image_attr = "photo"
    orderable = True
    description = "Les personnes présentées dans la section « L'équipe » de l'accueil. L'accueil affiche l'équipe de la saison en cours, ou à défaut la plus récente."

    def get_queryset(self, request):
        queryset = TeamMember.objects.select_related("season")
        season = request.GET.get("saison")
        if season:
            queryset = queryset.filter(season__label=season)
        return queryset.order_by("-season__start_date", "order", "pk")

    def extra_context(self, request):
        return {"seasons": Season.objects.all(), "selected_season": request.GET.get("saison", "")}


class TimelineCrud(Crud):
    model = TimelineEntry
    form_class = TimelineEntryForm
    name = "timeline"
    title = "Historique"
    singular = "étape de l'historique"
    icon = "history"
    columns = [("Date", "date_label"), ("Titre", "title"), ("Visible", "is_visible")]
    image_attr = "image"
    orderable = True
    description = "Le « carnet de bord » de l'accueil. Alterne photos réelles et visuels pour un rendu vivant."


class ServiceCrud(Crud):
    model = Service
    form_class = ServiceForm
    name = "services"
    title = "Services"
    singular = "service"
    icon = "sparkles"
    columns = [("Titre", "title"), ("Icône", "icon"), ("Visible", "is_visible")]
    orderable = True
    description = "Les cartes « Ce qu'on fait ensemble » de l'accueil."


class PageCrud(Crud):
    model = Page
    form_class = PageForm
    name = "pages"
    title = "Pages"
    singular = "page"
    icon = "file-text"
    columns = [("Titre", "title"), ("Adresse", "slug"), ("Publiée", "is_published"), ("À relire", "needs_review"), ("Modifiée le", "updated_at")]
    description = "Mentions légales, politique de confidentialité, conditions du magasin… Rédigées en Markdown."


class FAQCrud(Crud):
    model = FAQEntry
    form_class = FAQEntryForm
    name = "faq"
    title = "Questions fréquentes"
    singular = "question"
    icon = "circle-help"
    columns = [("Question", "question"), ("Thème", "topic"), ("Visible", "is_visible")]
    orderable = True
    description = "Affichées sur la page d'adhésion (thème « Adhésion »)."


class ResourceCrud(Crud):
    model = ResourceFile
    form_class = ResourceForm
    name = "resources"
    title = "Ressources membres"
    singular = "ressource"
    icon = "folder-open"
    capability = "resources"
    category = "resources"
    columns = [("Nom", "name"), ("Catégorie", "category"), ("Type", "extension")]
    description = "Documents et liens réservés aux membres connecté·es (stockés de façon privée)."
    back_url_name = "backoffice:dashboard"
    back_label = "Tableau de bord"

    def get_queryset(self, request):
        return ResourceFile.objects.order_by("category", "name")

    def extra_context(self, request):
        categories = ResourceFile.objects.exclude(category=None).exclude(category="").values_list("category", flat=True).distinct()
        return {"datalist_id": "resource-categories", "datalist": sorted(set(categories))}


class TagCrud(Crud):
    model = Tag
    form_class = TagForm
    name = "tags"
    title = "Catégories du magasin"
    singular = "catégorie"
    icon = "tag"
    capability = "warehouse"
    category = "warehouse"
    columns = [("Nom", "name"), ("Couleur", "color")]
    description = "Les étiquettes colorées qui servent à filtrer le catalogue du magasin."
    back_url_name = "backoffice:items"
    back_label = "Magasin"


team = TeamCrud()
timeline = TimelineCrud()
services = ServiceCrud()
pages = PageCrud()
faq = FAQCrud()
resources = ResourceCrud()
tags = TagCrud()
