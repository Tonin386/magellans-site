"""Fonctions utilitaires autour des personnes et des rôles du CA."""

from .models import Person


def board_people(*roles):
    """Personnes ayant au moins un des rôles CA donnés (filtrage en Python : indépendant de la base)."""
    wanted = set(roles)
    people = Person.objects.exclude(board_roles=[]).select_related("site_profile")
    return [person for person in people if wanted & set(person.board_roles or [])]


def board_emails(*roles):
    """Adresses e-mail des membres du CA actifs ayant l'un des rôles donnés."""
    emails = []
    for person in board_people(*roles):
        account = person.site_profile
        email = (account.email if account and account.is_active else None) or person.email
        if email:
            emails.append(email)
    return emails
