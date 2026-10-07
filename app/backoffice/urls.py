from django.urls import include, path

from . import content as crud
from .views import content, dashboard, finance, memberships, people, projects, warehouse

app_name = "backoffice"

urlpatterns = [
    path("", dashboard.dashboard, name="dashboard"),
    path("journal/", dashboard.activity, name="activity"),
    # Adhésions & saisons
    path("adhesions/", memberships.memberships, name="memberships"),
    path("adhesions/export.csv", memberships.memberships_export, name="memberships-export"),
    path("adhesions/nouvelle/", memberships.membership_create, name="membership-create"),
    path("adhesions/<int:pk>/", memberships.membership_edit, name="membership-edit"),
    path("adhesions/<int:pk>/inviter/", memberships.membership_invite, name="membership-invite"),
    path("adhesions/saisons/", memberships.seasons, name="seasons"),
    path("adhesions/saisons/nouvelle/", memberships.season_form, name="season-create"),
    path("adhesions/saisons/<int:pk>/", memberships.season_form, name="season-edit"),
    path("adhesions/saisons/<int:pk>/activer/", memberships.season_activate, name="season-activate"),
    path("adhesions/saisons/<int:pk>/synchroniser/", memberships.season_sync, name="season-sync"),
    path("adhesions/helloasso/", memberships.helloasso, name="helloasso"),
    # Personnes
    path("personnes/", people.people, name="people"),
    path("personnes/export.csv", people.people_export, name="people-export"),
    path("personnes/nouvelle/", people.person_create, name="person-create"),
    path("personnes/<int:pk>/", people.person_detail, name="person-detail"),
    path("personnes/<int:pk>/roles/", people.person_roles, name="person-roles"),
    path("personnes/<int:pk>/inviter/", people.person_invite, name="person-invite"),
    path("personnes/<int:pk>/associer/", people.person_link_account, name="person-link"),
    # Magasin
    path("magasin/", warehouse.items, name="items"),
    path("magasin/objets/nouveau/", warehouse.item_form, name="item-create"),
    path("magasin/objets/<int:pk>/", warehouse.item_form, name="item-edit"),
    path("magasin/objets/<int:pk>/archiver/", warehouse.item_archive, name="item-archive"),
    path("magasin/objets/<int:pk>/supprimer/", warehouse.item_delete, name="item-delete"),
    path("magasin/categories/", include(crud.tags.urls())),
    path("magasin/reservations/", warehouse.orders, name="orders"),
    path("magasin/reservations/cloture/", warehouse.orders_close_stale, name="orders-close-stale"),
    path("magasin/reservations/<int:pk>/", warehouse.order_manage, name="order-detail"),
    path("magasin/reservations/<int:pk>/lignes/<int:line_pk>/", warehouse.order_line_toggle, name="order-line"),
    path("magasin/reservations/<int:pk>/notes/", warehouse.order_notes, name="order-notes"),
    path("magasin/calendrier/", warehouse.calendar_view, name="calendar"),
    # Trésorerie
    path("tresorerie/", finance.finance, name="finance"),
    path("tresorerie/export.csv", finance.finance_export, name="finance-export"),
    path("tresorerie/operations/nouvelle/", finance.operation_form, name="operation-create"),
    path("tresorerie/operations/<str:pk>/", finance.operation_form, name="operation-edit"),
    path("tresorerie/notes-de-frais/", finance.invoices, name="invoices"),
    path("tresorerie/notes-de-frais/<int:pk>/", finance.invoice_manage, name="invoice-detail"),
    # Projets & aides
    path("projets/", projects.projects, name="projects"),
    path("projets/nouveau/", projects.project_form, name="project-create"),
    path("projets/<int:pk>/", projects.project_form, name="project-edit"),
    path("projets/<int:pk>/supprimer/", projects.project_delete, name="project-delete"),
    path("projets/<int:pk>/generique/", projects.project_credit_add, name="project-credit-add"),
    path("projets/<int:pk>/generique/<int:credit_pk>/supprimer/", projects.project_credit_delete, name="project-credit-delete"),
    path("aides/", projects.funding, name="funding"),
    path("aides/<int:pk>/", projects.funding_manage, name="funding-detail"),
    # Ressources
    path("ressources/", include(crud.resources.urls())),
    # Contenus du site
    path("contenus/", content.content_hub, name="content"),
    path("contenus/parametres/", content.site_settings, name="settings"),
    path("contenus/parametres/<slug:section>/", content.site_settings, name="settings-section"),
    path("contenus/equipe/copier/", content.team_copy, name="team-copy"),
    path("contenus/equipe/", include(crud.team.urls())),
    path("contenus/historique/", include(crud.timeline.urls())),
    path("contenus/services/", include(crud.services.urls())),
    path("contenus/pages/", include(crud.pages.urls())),
    path("contenus/faq/", include(crud.faq.urls())),
]
