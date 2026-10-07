# Exploitation du serveur magellans.fr

Tout se pilote depuis le serveur avec `./run.sh` (dans `/home/ubuntu/magellans-site`,
accès : `ssh magellans`). `./run.sh help` liste les commandes.

## Architecture

```
Internet ──► nginx (443, certificats Let's Encrypt)
               ├─ /media/       fichiers publics          ← app/media/
               ├─ /_protected/  fichiers privés (interne)  ← app/private/  (servis après contrôle des droits)
               └─ /             django (gunicorn)          ── postgres (volume magellans-site_postgres_data_django)
```

- **Code** : identique à la branche `production` du dépôt GitHub. Le serveur ne doit porter
  aucune modification locale : `./run.sh deploy` refuse de s'exécuter sinon.
- **Configuration et secrets** : `app/.env` (jamais versionné, modèle : `app/.env.example`).
- **Données** : base PostgreSQL (volume Docker), `app/media/` (affiches, photos…),
  `app/private/` (justificatifs, dossiers d'aide, contrats signés, ressources membres).
- **Sauvegardes** : `backups/` ; **journaux des tâches automatiques** : `logs/`.

## Tâches automatiques (cron de l'utilisateur `ubuntu`)

Installées ou mises à jour par `./run.sh cron` (`crontab -l` pour les voir). Heures UTC.

| Quand | Commande | Rôle |
| --- | --- | --- |
| toutes les 5 min | `watchdog` | Si le site ne répond plus deux fois de suite : redémarrage automatique + e-mail au webmaster |
| toutes les 10 min | `autodeploy` | Si `origin/production` a avancé : déploiement complet |
| chaque nuit 01:15 | `backup` | Sauvegarde vérifiée de la base (30 jours, au moins les 10 dernières) |
| dimanche 01:45 | `backup --media` | Archive des fichiers (les 4 dernières) |
| le 1er du mois 02:30 | `check-backup` | Restaure la dernière sauvegarde dans une base jetable pour prouver qu'elle est exploitable |
| toutes les 6 h | `sync` | Synchronisation des adhésions HelloAsso (filet de sécurité du webhook) |
| lundi 03:30 | `maintenance` | Sessions expirées, images Docker inutiles, journaux ; alerte si le certificat expire dans moins de 14 jours ou si le disque dépasse 85 % |

Les alertes partent par e-mail vers les membres du CA ayant le rôle **Webmaster**
(à défaut, vers l'adresse de contact), via le SMTP Google configuré dans `app/.env`.

Le certificat HTTPS de `magellans.fr` (Let's Encrypt, validation HTTP-01) est renouvelé
par le timer systemd de certbot : les jetons de validation sont écrits dans `nginx/acme/`,
que nginx sert sur `http://magellans.fr/.well-known/acme-challenge/`. Le hook
`/etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh` recharge nginx après chaque
renouvellement. Test sans risque : `sudo certbot renew --dry-run`.

Pour couvrir aussi `www.magellans.fr`, faire d'abord pointer son enregistrement DNS vers le
serveur, puis :
`sudo certbot certonly --webroot -w /home/ubuntu/magellans-site/nginx/acme --cert-name magellans.fr -d magellans.fr -d www.magellans.fr`

## Déployer une nouvelle version

Rien à faire sur le serveur : pousser sur `production` (depuis un poste de dev,
`./run.sh gitupdate` publie `dev` → `production` → `main`). Dans les 10 minutes :

1. sauvegarde vérifiée de la base ;
2. `git pull --ff-only`, construction de l'image ;
3. redémarrage (les migrations s'appliquent au démarrage du conteneur) ;
4. contrôle du site (application + nginx) ;
5. en cas d'échec au démarrage : retour automatique au commit précédent, reconstruction,
   e-mail d'alerte ;
6. si la construction de l'image échoue (souvent un incident réseau passager), le code
   revient à la version en service et un nouvel essai a lieu au passage suivant ; e-mail
   d'alerte au 3e échec consécutif.

La version réellement en service est notée dans `logs/version-en-ligne` (`./run.sh status`
affiche la version du code). Pour déployer tout de suite : `./run.sh deploy`.
Journal : `logs/deploy.log`.

## Sauvegardes et restauration

```bash
./run.sh backup             # base, vérifiée par pg_restore --list
./run.sh backup --media     # + fichiers publics et privés
./run.sh check-backup       # teste la restauration de la dernière sauvegarde (base jetable)
./run.sh restore backups/base-AAAAMMJJ-HHMMSS.dump   # sauvegarde l'état actuel, puis remplace la base
```

Les sauvegardes restent sur le serveur : en copier régulièrement une hors du serveur, par
exemple depuis un ordinateur :

```bash
rsync -a magellans:magellans-site/backups/ ~/magellans-backups/serveur/
```

## Retour arrière manuel

```bash
git log --oneline -5                     # repérer la version voulue
git reset --hard <commit> && ./run.sh deploy --no-pull
./run.sh restore backups/base-….dump     # seulement si les données doivent aussi revenir en arrière
```

Penser ensuite à remettre la branche `production` du dépôt au même commit, sinon
`autodeploy` redéploiera la version la plus récente.

## Configuration HelloAsso

- Saisons et campagnes : espace CA → Adhésions → Saisons (coller l'adresse de la campagne).
  Si une campagne est recréée en cours de saison, coller l'ancienne dans « Autres campagnes
  HelloAsso de la saison » (cas de 2023-2024).
- Historique : les saisons 2021-2022 à 2024-2025 sont liées à leurs campagnes ; leurs
  adhésions se récupèrent avec `./run.sh sync --all` (saison terminée : ni compte créé, ni e-mail).
- Webhook : dans le back-office HelloAsso (Mon compte → Intégrations et API → Notifications),
  renseigner `https://magellans.fr/api/helloasso/<HELLOASSO_WEBHOOK_SECRET>/`
  (valeur dans `app/.env`). Chaque notification est de toute façon revérifiée auprès de l'API.
- Identifiants API : `HELLOASSO_CLIENTID` / `HELLOASSO_CLIENTSECRET` dans `app/.env`.

## Installer un nouveau serveur

```bash
git clone -b production git@github.com:Tonin386/magellans-site.git && cd magellans-site
cp app/.env.example app/.env && nano app/.env      # secrets, NGINX_CONF_FILE=conf_ssl.d
./run.sh restore <sauvegarde>.dump                  # ou une base neuve : ./run.sh up
tar -xzf <archive fichiers>.tar.gz                  # app/media et app/private
./run.sh up && ./run.sh cron
```

## Historique : mise à niveau de 2026

Le 7 octobre 2026, l'ancien site (Django 5.2, migrations générées sur le serveur, médias
dans `app/assets/media`) a été remplacé par la refonte. La procédure, répétée au préalable
sur une copie de la base de production, a été :

1. sauvegardes complètes (sur le serveur et hors serveur) ;
2. mise de côté des migrations non versionnées de l'ancien serveur, déplacement des médias
   (`app/assets/media` → `app/media`), `git pull` ;
3. `./run.sh upgrade` : alignement de l'historique des migrations (`baseline_migrations`,
   qui ne touche que la table `django_migrations`), migrations additives uniquement, mise à
   l'abri des fichiers privés (`secure_private_media`), synchronisation HelloAsso.

Les données d'origine ont été vérifiées identiques avant et après (empreintes de toutes les
tables). Les sauvegardes d'avant la mise à niveau sont dans `backups/avant-refonte-2026/`.
