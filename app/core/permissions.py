"""Rôles du conseil d'administration et droits associés.

Une personne peut cumuler plusieurs rôles (ex. « Secrétaire et magasinière »).
Les vues de l'espace CA vérifient des *capacités* (``warehouse``, ``finance``…)
plutôt que des rôles : la correspondance est centralisée ici.
"""

from functools import wraps

from django.core.exceptions import PermissionDenied

BOARD_ROLES = [
    ("P", "Président·e"),
    ("V", "Vice-président·e"),
    ("T", "Trésorier·ère"),
    ("S", "Secrétaire"),
    ("G", "Gestionnaire du magasin"),
    ("C", "Communication"),
    ("W", "Webmaster"),
    ("A", "Administrateur·ice"),
]
BOARD_ROLE_LABELS = dict(BOARD_ROLES)
ALL_BOARD = frozenset(BOARD_ROLE_LABELS)

# Rôles « historiques » (champ Person.role avant la refonte) correspondant au CA.
LEGACY_BOARD_ROLES = {"P", "C", "G", "T", "S", "W"}

CAPABILITIES = {
    # Accès à l'espace CA et consultation générale
    "backoffice": ALL_BOARD,
    "memberships": ALL_BOARD,
    "people": ALL_BOARD,
    "projects": ALL_BOARD,
    "funding": ALL_BOARD,
    "resources": ALL_BOARD,
    "content": ALL_BOARD,
    "audit": ALL_BOARD,
    # Droits sensibles
    "roles": frozenset({"P", "V", "W"}),
    "warehouse": frozenset({"P", "V", "G", "W"}),
    "finance": frozenset({"P", "V", "T"}),
    "finance_edit": frozenset({"T"}),
    "funding_decide": frozenset({"P", "V", "T"}),
    "settings_advanced": frozenset({"P", "W"}),
}

CAPABILITY_LABELS = {
    "backoffice": "Accéder à l'espace CA",
    "memberships": "Gérer les adhésions et les saisons",
    "people": "Consulter et modifier les fiches personnes",
    "projects": "Gérer les projets",
    "funding": "Consulter les demandes d'aide",
    "resources": "Gérer les ressources membres",
    "content": "Modifier les contenus du site",
    "audit": "Consulter le journal d'activité",
    "roles": "Attribuer les rôles du CA",
    "warehouse": "Gérer le magasin et les réservations",
    "finance": "Consulter la trésorerie",
    "finance_edit": "Saisir des opérations et traiter les notes de frais",
    "funding_decide": "Statuer sur les demandes d'aide",
    "settings_advanced": "Paramètres avancés (maintenance, statistiques, webhook)",
}


def user_board_roles(user):
    """Rôles CA de l'utilisateur (ensemble de codes), mis en cache sur l'objet."""
    if not getattr(user, "is_authenticated", False):
        return frozenset()
    cached = getattr(user, "_board_roles_cache", None)
    if cached is not None:
        return cached
    person = getattr(user, "site_person", None)
    roles = frozenset(r for r in (getattr(person, "board_roles", None) or []) if r in ALL_BOARD)
    user._board_roles_cache = roles
    return roles


def has_capability(user, capability):
    if not getattr(user, "is_authenticated", False) or not user.is_active:
        return False
    if user.is_superuser:
        return True
    allowed = CAPABILITIES.get(capability)
    if allowed is None:
        raise KeyError(f"Capacité inconnue : {capability}")
    return bool(user_board_roles(user) & allowed)


def user_capabilities(user):
    return {cap for cap in CAPABILITIES if has_capability(user, cap)}


def capability_required(*capabilities):
    """Décorateur de vue : connexion obligatoire + au moins une des capacités."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.contrib.auth.views import redirect_to_login

                return redirect_to_login(request.get_full_path())
            if not any(has_capability(request.user, cap) for cap in capabilities):
                raise PermissionDenied("Espace réservé au conseil d'administration.")
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def require_capability(user, capability):
    if not has_capability(user, capability):
        raise PermissionDenied
