"""CRUD générique pour les contenus simples de l'espace CA (équipe, historique, FAQ…)."""

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path, reverse
from django.views.decorators.http import require_POST

from core.audit import log_activity
from core.http import smart_redirect
from core.permissions import capability_required, has_capability


class Crud:
    """Déclare un ensemble de vues liste / création / édition / suppression / tri."""

    model = None
    form_class = None
    name = ""  # préfixe des noms d'URL (ex. "team")
    title = ""  # titre de la liste
    singular = ""  # « un membre de l'équipe »
    icon = "pen-line"
    capability = "content"
    category = "content"
    columns = []  # [(libellé, attribut)]
    image_attr = ""  # vignette dans la liste
    orderable = False
    description = ""
    back_url_name = "backoffice:content"
    back_label = "Contenus du site"

    def get_queryset(self, request):
        return self.model._default_manager.all()

    def form_kwargs(self, request, instance=None):
        return {}

    def extra_context(self, request):
        return {}

    # -------------------------------------------------------------------- Vues
    def list_view(self, request):
        objects = list(self.get_queryset(request))
        rows = [
            {"obj": obj, "cells": [self._cell(obj, attr) for _label, attr in self.columns], "image": self._image(obj)}
            for obj in objects
        ]
        return render(
            request,
            "backoffice/crud/list.html",
            {"crud": self, "rows": rows, "headers": [label for label, _ in self.columns], **self.extra_context(request)},
        )

    def form_view(self, request, pk=None):
        instance = get_object_or_404(self.get_queryset(request), pk=pk) if pk else None
        form = self.form_class(request.POST or None, request.FILES or None, instance=instance, **self.form_kwargs(request, instance))
        if request.method == "POST" and form.is_valid():
            with transaction.atomic():
                obj = form.save()
                if hasattr(obj, "updated_by_id"):
                    type(obj).objects.filter(pk=obj.pk).update(updated_by=request.user)
            verb = "updated" if instance else "created"
            log_activity(
                request,
                f"{self.name}-{verb}",
                f"{self.singular.capitalize()} {'modifié·e' if instance else 'ajouté·e'} : {obj}.",
                target=obj,
                category=self.category,
                data={"champs": sorted(form.changed_data)},
            )
            messages.success(request, "Modifications enregistrées." if instance else f"{self.singular.capitalize()} ajouté·e.")
            return redirect(f"backoffice:{self.name}")
        return render(
            request,
            "backoffice/crud/form.html",
            {"crud": self, "form": form, "object": instance, **self.extra_context(request)},
        )

    def delete_view(self, request, pk):
        obj = get_object_or_404(self.get_queryset(request), pk=pk)
        label = str(obj)
        obj.delete()
        log_activity(request, f"{self.name}-deleted", f"{self.singular.capitalize()} supprimé·e : {label}.", category=self.category)
        messages.success(request, f"« {label} » a été supprimé·e.")
        return smart_redirect(request, f"backoffice:{self.name}")

    def reorder_view(self, request):
        ids = [int(value) for value in request.POST.getlist("ids") if value.isdigit()]
        with transaction.atomic():
            for position, pk in enumerate(ids):
                self.model._default_manager.filter(pk=pk).update(order=position)
        log_activity(request, f"{self.name}-reordered", f"Nouvel ordre : {self.title.lower()}.", category=self.category)
        return HttpResponse(status=204)

    # -------------------------------------------------------------- Aides
    def _cell(self, obj, attr):
        value = getattr(obj, attr, "")
        if callable(value):
            value = value()
        if hasattr(obj, f"get_{attr}_display"):
            value = getattr(obj, f"get_{attr}_display")()
        if isinstance(value, bool):
            return "✓" if value else "—"
        return value if value not in (None, "") else "—"

    def _image(self, obj):
        if not self.image_attr:
            return None
        field_file = getattr(obj, self.image_attr, None)
        return field_file.url if field_file else ""

    def urls(self):
        guard = capability_required(self.capability)
        return [
            path("", guard(self.list_view), name=self.name),
            path("nouveau/", guard(self.form_view), name=f"{self.name}-create"),
            path("<int:pk>/", guard(self.form_view), name=f"{self.name}-edit"),
            path("<int:pk>/supprimer/", guard(require_POST(self.delete_view)), name=f"{self.name}-delete"),
            path("ordre/", guard(require_POST(self.reorder_view)), name=f"{self.name}-reorder"),
        ]

    @property
    def list_url(self):
        return reverse(f"backoffice:{self.name}")

    @property
    def create_url(self):
        return reverse(f"backoffice:{self.name}-create")

    @property
    def reorder_url(self):
        return reverse(f"backoffice:{self.name}-reorder")

    @property
    def back_url(self):
        return reverse(self.back_url_name)
