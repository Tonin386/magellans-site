"""Client minimal de l'API HelloAsso v5 (https://dev.helloasso.com)."""

import logging

import httpx
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger("magellans.helloasso")
TOKEN_CACHE_KEY = "helloasso:access-token"


class HelloAssoError(Exception):
    pass


class HelloAssoClient:
    def __init__(self, conf=None, transport=None):
        self.conf = conf or settings.HELLOASSO
        self.base = self.conf["API_URL"]
        self.transport = transport  # permet d'injecter un faux serveur dans les tests

    @property
    def configured(self):
        return bool(self.conf.get("CLIENT_ID") and self.conf.get("CLIENT_SECRET"))

    def _client(self):
        return httpx.Client(
            timeout=20,
            transport=self.transport,
            headers={"User-Agent": "magellans-site/2026 (+https://magellans.fr)"},
        )

    def token(self, force=False):
        if not self.configured:
            raise HelloAssoError("Identifiants de l'API HelloAsso non configurés (HELLOASSO_CLIENTID / HELLOASSO_CLIENTSECRET).")
        if not force:
            cached = cache.get(TOKEN_CACHE_KEY)
            if cached:
                return cached
        try:
            with self._client() as client:
                response = client.post(
                    f"{self.base}/oauth2/token",
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.conf["CLIENT_ID"],
                        "client_secret": self.conf["CLIENT_SECRET"],
                    },
                )
        except httpx.HTTPError as error:
            raise HelloAssoError(f"HelloAsso injoignable : {error}") from error
        if response.status_code != 200:
            raise HelloAssoError(f"Authentification HelloAsso refusée ({response.status_code}).")
        payload = response.json()
        token = payload["access_token"]
        cache.set(TOKEN_CACHE_KEY, token, max(60, int(payload.get("expires_in", 1800)) - 120))
        return token

    def get(self, path, params=None):
        for attempt in range(2):
            token = self.token(force=attempt > 0)
            try:
                with self._client() as client:
                    response = client.get(
                        f"{self.base}/v5/{path.lstrip('/')}",
                        params=params,
                        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
                    )
            except httpx.HTTPError as error:
                raise HelloAssoError(f"HelloAsso injoignable : {error}") from error
            if response.status_code == 401 and attempt == 0:
                cache.delete(TOKEN_CACHE_KEY)
                continue
            if response.status_code == 404:
                raise HelloAssoError("Élément introuvable sur HelloAsso (404).")
            if response.status_code >= 400:
                raise HelloAssoError(f"Erreur de l'API HelloAsso ({response.status_code}).")
            return response.json()
        raise HelloAssoError("Authentification HelloAsso impossible.")

    # ------------------------------------------------------------------ Raccourcis
    def order(self, order_id):
        return self.get(f"orders/{int(order_id)}")

    def form_public(self, organization, form_type, form_slug):
        return self.get(f"organizations/{organization}/forms/{form_type}/{form_slug}/public")

    def form_items(self, organization, form_type, form_slug, page_size=100):
        """Toutes les lignes (adhésions, dons…) d'une campagne, page par page."""
        params = {"pageSize": page_size, "withDetails": "true"}
        seen = set()
        while True:
            payload = self.get(f"organizations/{organization}/forms/{form_type}/{form_slug}/items", params=params)
            data = payload.get("data") or []
            if not data:
                break
            fresh = [item for item in data if item.get("id") not in seen]
            if not fresh:
                break
            for item in fresh:
                seen.add(item.get("id"))
                yield item
            token = (payload.get("pagination") or {}).get("continuationToken")
            if not token or len(data) < page_size:
                break
            params = {**params, "continuationToken": token}
