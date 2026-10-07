from django.conf import settings
from django.utils.functional import SimpleLazyObject

from .models import Page, SiteSettings
from .permissions import user_board_roles, user_capabilities


def site(request):
    """Variables disponibles dans tous les gabarits."""
    from memberships.models import Season

    user = getattr(request, "user", None)

    def membership():
        if not (user and user.is_authenticated):
            return None
        from memberships.models import Membership

        person = getattr(user, "site_person", None)
        season = Season.current()
        if person is None or season is None:
            return None
        return Membership.objects.active().filter(person=person, season=season).first()

    return {
        "site": SimpleLazyObject(SiteSettings.load),
        "current_season": SimpleLazyObject(Season.current),
        "footer_pages": SimpleLazyObject(
            lambda: list(Page.objects.filter(is_published=True, show_in_footer=True).only("slug", "title"))
        ),
        "caps": SimpleLazyObject(lambda: user_capabilities(user) if user else set()),
        "board_roles": SimpleLazyObject(lambda: user_board_roles(user) if user else frozenset()),
        "my_membership": SimpleLazyObject(membership),
        "SITE_URL": settings.SITE_URL,
    }
