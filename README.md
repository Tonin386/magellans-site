# Magellans — le site internet

Code du site [magellans.fr](https://magellans.fr) de l'association audiovisuelle Magellans :
vitrine publique (films, équipe, adhésion HelloAsso), espace membres (magasin de matériel,
notes de frais, aides à projet, ressources) et espace CA (adhésions, personnes, réservations,
trésorerie, contenus du site, paramètres).

- **Exploitation du serveur, déploiement, sauvegardes** : voir [DEPLOIEMENT.md](DEPLOIEMENT.md).

## Technologies

| Côté | Outils |
| --- | --- |
| Serveur | Django 6.1 (Python 3.14), PostgreSQL 16, gunicorn, WhiteNoise, WeasyPrint (contrats PDF) |
| Interface | Gabarits Django + [django-cotton](https://django-cotton.com) (composants), HTMX 2, Alpine.js (version CSP), Tailwind CSS 4, TypeScript, Vite 8 |
| Paiements | API HelloAsso v5 (adhésions synchronisées + webhook vérifié) |
| Production | Docker Compose (postgres, django, nginx), Let's Encrypt, tâches cron pilotées par `run.sh` |

## Organisation du code (`app/`)

| Application | Rôle |
| --- | --- |
| `core` | Paramètres du site, permissions du CA, pages, e-mails, fichiers privés, journal d'activité, composants d'interface |
| `members` | Comptes, profils, fiches personnes, annuaire, connexion / inscription |
| `memberships` | Saisons, adhésions, synchronisation HelloAsso |
| `showcase` | Pages publiques (accueil, films, adhésion, contact) |
| `warehouse` | Magasin : catalogue, réservations, disponibilités, contrats signés en ligne |
| `bank` | Trésorerie et notes de frais |
| `dashboard` | Projets, aides à projet, ressources membres |
| `backoffice` | Espace CA (`/espace-ca/`) |
| `api` | Webhook HelloAsso, notifications de l'ancien site |
| `frontend/` | Sources TypeScript / CSS compilées par Vite (`frontend/dist`, non versionné) |

Les rôles du CA (présidence, trésorerie, magasin, webmaster…) donnent des droits précis,
définis dans `core/permissions.py`.

## Développer en local

Prérequis : Python 3.14, Node 22, Docker (pour PostgreSQL).

```bash
# Base de données de développement
docker run -d --name magellans-pg-dev -p 127.0.0.1:5432:5432 \
  -e POSTGRES_DB=magellans -e POSTGRES_USER=magellans -e POSTGRES_PASSWORD=magellans postgres:16-bullseye

# Python
python3.14 -m venv .venv && .venv/bin/pip install -r app/requirements.txt
cp app/.env.example app/.env    # puis : DEBUG=1, DB_HOST=127.0.0.1, DB_PASSWORD=magellans…

# Interface (Vite) — dans un second terminal : npm run dev (et VITE_DEV_MODE=1 dans app/.env)
cd app/frontend && npm ci && npm run build && cd ..

.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_demo     # données fictives (refusé si DEBUG=0)
.venv/bin/python manage.py runserver
```

Comptes de démonstration créés par `seed_demo` : `admin@magellans.test` (CA) et
`membre@magellans.test`, mot de passe `magellans-demo`. Sans `DB_HOST`, une base SQLite est
utilisée. Sans `EMAIL_HOST`, les e-mails s'affichent dans la console.

Commandes utiles :

```bash
python manage.py helloasso_sync [--all] [--invite]   # adhésions HelloAsso
python manage.py makemigrations --check               # aucune migration oubliée
cd frontend && npm run typecheck                      # TypeScript
```

Les icônes (sprite `app/static/icons.svg`) sont générées par `npm run icons` à partir des
`{% icon "nom" %}` trouvés dans les gabarits : relancer la commande après en avoir ajouté.

## Publier une modification

1. Travailler sur la branche `dev`, pousser.
2. `./run.sh gitupdate` publie `dev` → `production` → `main`.
3. Le serveur déploie tout seul la branche `production` dans les 10 minutes
   (sauvegarde, construction, contrôle, retour arrière automatique en cas d'échec).

Les migrations doivent rester **additives** (nouvelles tables ou colonnes) : la base de
production contient l'historique de l'association depuis 2023.
