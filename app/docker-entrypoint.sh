#!/bin/sh
# Point d'entrée du conteneur Django.
# - prépare les dossiers de données (volumes) pour l'utilisateur applicatif ;
# - refuse de démarrer si la base n'a pas encore été mise à niveau (refonte 2026) ;
# - applique les migrations (uniquement additives), puis lance le serveur.
set -e

APP_UID=1000
run_as_app() { setpriv --reuid=$APP_UID --regid=$APP_UID --init-groups "$@"; }

for dir in /app/media /app/private /app/backups; do
    mkdir -p "$dir"
    if [ "$(stat -c %u "$dir")" != "$APP_UID" ]; then
        chown -R $APP_UID:$APP_UID "$dir"
    fi
done

if [ "${SKIP_MIGRATIONS:-0}" != "1" ] && [ "$1" = "gunicorn" ]; then
    if ! run_as_app python manage.py baseline_migrations --status; then
        echo "⛔ La base de données n'a pas encore été mise à niveau pour la nouvelle version du site."
        echo "   Lancez depuis le serveur : ./run.sh upgrade (sauvegarde, puis mise à niveau)."
        exit 1
    fi
    run_as_app python manage.py migrate --noinput
    run_as_app python manage.py createcachetable
fi

exec setpriv --reuid=$APP_UID --regid=$APP_UID --init-groups "$@"
