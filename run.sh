#!/usr/bin/env bash
# =============================================================================
#  Site magellans.fr — pilotage du serveur (voir DEPLOIEMENT.md)
#
#  Déploiement
#    ./run.sh deploy          Sauvegarde vérifiée, git pull, build, redémarrage, contrôle
#                             (retour arrière automatique si le site ne répond plus)
#    ./run.sh autodeploy      Déploie seulement si la branche suivie a avancé (cron)
#    ./run.sh upgrade         Mise à niveau UNIQUE de l'ancien site (déjà faite en 2026)
#
#  Sauvegardes
#    ./run.sh backup [--media]   Sauvegarde vérifiée de la base (+ fichiers)
#    ./run.sh check-backup [F]   Restaure une sauvegarde dans une base jetable pour la tester
#    ./run.sh restore F          Remplace la base par une sauvegarde (confirmation demandée)
#
#  Exploitation
#    ./run.sh cron            Installe / met à jour les tâches automatiques
#    ./run.sh watchdog        Redémarre le site s'il ne répond plus (cron, toutes les 5 min)
#    ./run.sh maintenance     Ménage hebdomadaire + alertes (certificat, disque)
#    ./run.sh sync            Synchronise les adhésions HelloAsso
#    ./run.sh up | down | restart | status | logs [service] | shell | python | manage <cmd>
#    ./run.sh gitupdate       (poste de dev) publie dev → production → main
#
#  Option globale : --yes   répond « oui » aux confirmations.
# =============================================================================
set -Eeuo pipefail
cd "$(dirname "$0")"
ROOT="$(pwd)"

ENV_FILE="app/.env"
BACKUP_DIR="backups"
LOG_DIR="logs"
PID_FILE="pids.txt"
DEPLOY_BRANCH="${DEPLOY_BRANCH:-production}"
SITE_DOMAIN="${SITE_DOMAIN:-magellans.fr}"
KEEP_DB_DAYS=30       # bases : 30 jours…
KEEP_DB_MIN=10        # …et toujours au moins les 10 dernières
KEEP_MEDIA=4          # archives de fichiers conservées
DEPLOYED_FILE="$LOG_DIR/version-en-ligne"  # commit réellement en service
LAST_BACKUP=""
ASSUME_YES=0
COMPOSE=(docker compose --env-file "$ENV_FILE")

args=()
for arg in "$@"; do
  if [ "$arg" = "--yes" ]; then ASSUME_YES=1; else args+=("$arg"); fi
done
set -- "${args[@]+"${args[@]}"}"

if [ -t 1 ]; then
  red()   { printf '\033[31m%s\033[0m\n' "$*"; }
  green() { printf '\033[32m%s\033[0m\n' "$*"; }
  info()  { printf '\033[36m▸ %s\033[0m\n' "$*"; }
else  # journaux de cron : horodatés, sans couleurs
  red()   { printf '%s ✖ %s\n' "$(date '+%F %T')" "$*"; }
  green() { printf '%s ✔ %s\n' "$(date '+%F %T')" "$*"; }
  info()  { printf '%s ▸ %s\n' "$(date '+%F %T')" "$*"; }
fi
die() { red "✖ $*"; exit 1; }
trap 'red "Erreur (ligne $LINENO). Dernière sauvegarde : ${LAST_BACKUP:-aucune}. Voir DEPLOIEMENT.md."' ERR

[ -f "$ENV_FILE" ] || die "Fichier $ENV_FILE introuvable (voir app/.env.example)."

# Lit une variable de app/.env sans interpréter le fichier (les secrets peuvent contenir $, ', &…).
env_value() {
  local line
  line=$(grep -E "^[[:space:]]*$1=" "$ENV_FILE" | tail -n 1 || true)
  line=${line#*=}
  line=${line%$'\r'}
  if [ ${#line} -ge 2 ] && { [[ $line == \"*\" ]] || [[ $line == \'*\' ]]; }; then
    line=${line:1:${#line}-2}
  fi
  printf '%s' "$line"
}
DB_DJANGO_NAME=$(env_value DB_DJANGO_NAME)
DB_USER=$(env_value DB_USER)
DB_PASSWORD=$(env_value DB_PASSWORD)
DEBUG=$(env_value DEBUG)
NGINX_CONF_FILE=$(env_value NGINX_CONF_FILE)
[ -n "$DB_DJANGO_NAME" ] || die "DB_DJANGO_NAME manquant dans $ENV_FILE"
[ -n "$DB_USER" ] || die "DB_USER manquant dans $ENV_FILE"
mkdir -p "$BACKUP_DIR" "$LOG_DIR"

confirm() {
  [ "$ASSUME_YES" = 1 ] && return 0
  read -r -p "$1 [o/N] " answer
  [[ "$answer" =~ ^[oOyY]$ ]]
}

# Un seul traitement lourd à la fois (déploiement, sauvegarde, surveillance…).
lock() {
  exec 9>"$LOG_DIR/.run.lock"
  if [ "${1:-wait}" = "try" ]; then flock -n 9; else flock -w 1800 9 || die "Une autre opération est en cours."; fi
}

# Conteneur ponctuel (fonctionne même site arrêté) / conteneur en marche.
manage() { "${COMPOSE[@]}" run --rm -T -e SKIP_MIGRATIONS=1 django python manage.py "$@"; }
in_django() {
  local flags=(-u magellans)  # comme le site : les fichiers créés (bannières…) lui appartiennent
  { [ -t 0 ] && [ -t 1 ]; } || flags+=(-T)  # pas de terminal (cron) : pas de TTY
  "${COMPOSE[@]}" exec "${flags[@]}" django python manage.py "$@"
}

# Prévient le webmaster par e-mail (sans jamais faire échouer l'appelant).
alert() {
  red "ALERTE : $1 — $2"
  "${COMPOSE[@]}" exec -T django python manage.py alert "$1" "$2" >/dev/null 2>&1 \
    || manage alert "$1" "$2" >/dev/null 2>&1 || true
}

# ------------------------------------------------------------------ Sauvegardes
backup_db() {
  local file
  file="$BACKUP_DIR/base-$(date +%Y%m%d-%H%M%S).dump"
  info "Sauvegarde de la base « $DB_DJANGO_NAME » → $file"
  "${COMPOSE[@]}" up -d postgres-django >/dev/null 2>&1
  for _ in $(seq 1 30); do
    "${COMPOSE[@]}" exec -T postgres-django pg_isready -U "$DB_USER" -d "$DB_DJANGO_NAME" >/dev/null 2>&1 && break
    sleep 2
  done
  "${COMPOSE[@]}" exec -T postgres-django pg_dump -U "$DB_USER" -d "$DB_DJANGO_NAME" -Fc --no-owner > "$file" \
    || { rm -f "$file"; die "pg_dump a échoué : aucune opération n'a été faite."; }
  # Vérification : le fichier doit être lisible par pg_restore et contenir des données.
  local tables
  tables=$("${COMPOSE[@]}" exec -T postgres-django pg_restore --list < "$file" | grep -c "TABLE DATA" || true)
  if [ ! -s "$file" ] || [ "${tables:-0}" -lt 5 ]; then
    die "Sauvegarde invalide ($file) : arrêt par sécurité."
  fi
  chmod 600 "$file"
  green "Sauvegarde vérifiée : $file ($(du -h "$file" | cut -f1), $tables tables)"
  LAST_BACKUP="$file"
  prune_backups
}

backup_media() {
  local file
  file="$BACKUP_DIR/fichiers-$(date +%Y%m%d-%H%M%S).tar.gz"
  local dirs=()
  for dir in app/media app/private app/assets/media; do [ -d "$dir" ] && dirs+=("$dir"); done
  if [ ${#dirs[@]} -eq 0 ]; then info "Aucun fichier à sauvegarder."; return; fi
  info "Sauvegarde des fichiers (${dirs[*]}) → $file"
  tar -czf "$file" "${dirs[@]}"
  chmod 600 "$file"
  green "Fichiers sauvegardés : $file ($(du -h "$file" | cut -f1))"
  prune_backups
}

# Fichiers d'un motif donné, du plus récent au plus ancien.
backups_by_date() {
  find "$BACKUP_DIR" -maxdepth 1 -name "$1" -printf '%T@ %p\n' | sort -rn | cut -d' ' -f2-
}

prune_backups() {
  local files file
  # Bases : les KEEP_DB_MIN plus récentes sont toujours gardées, les autres pendant KEEP_DB_DAYS jours.
  mapfile -t files < <(backups_by_date 'base-*.dump')
  for file in "${files[@]:KEEP_DB_MIN}"; do
    if [ -n "$(find "$file" -mtime +"$KEEP_DB_DAYS")" ]; then rm -f "$file"; fi
  done
  mapfile -t files < <(backups_by_date 'fichiers-*.tar.gz')
  for file in "${files[@]:KEEP_MEDIA}"; do rm -f "$file"; done
}

latest_backup() {
  backups_by_date 'base-*.dump' | awk 'NR == 1'
}

restore_db() {
  local file="${1:-}"
  [ -f "$file" ] || die "Indiquez un fichier de sauvegarde existant (ex. backups/base-….dump)."
  red "⚠ La base « $DB_DJANGO_NAME » va être REMPLACÉE par le contenu de $file."
  confirm "Confirmer la restauration ?" || die "Restauration annulée."
  backup_db
  info "(Une sauvegarde de l'état actuel a été faite avant : $LAST_BACKUP)"
  "${COMPOSE[@]}" stop django nginx || true
  "${COMPOSE[@]}" exec -T postgres-django pg_restore -U "$DB_USER" -d "$DB_DJANGO_NAME" --clean --if-exists --no-owner < "$file"
  "${COMPOSE[@]}" up -d
  green "Base restaurée depuis $file"
}

cmd_check_backup() {
  # Restaure une sauvegarde dans une base jetable : prouve qu'elle est réellement exploitable.
  local dump="${1:-$(latest_backup)}" name="magellans-verification" network
  [ -f "$dump" ] || die "Sauvegarde introuvable : ${dump:-aucune}"
  network=$(docker inspect magellans-django-pgsql --format '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{end}}')
  docker rm -f "$name" >/dev/null 2>&1 || true
  docker run -d --name "$name" --network "$network" -e POSTGRES_DB="$DB_DJANGO_NAME" -e POSTGRES_USER="$DB_USER" \
    -e POSTGRES_PASSWORD="$DB_PASSWORD" postgres:16-bullseye >/dev/null
  trap 'docker rm -f magellans-verification >/dev/null 2>&1 || true' EXIT
  for _ in $(seq 1 30); do docker exec "$name" pg_isready -U "$DB_USER" -d "$DB_DJANGO_NAME" >/dev/null 2>&1 && break; sleep 2; done
  sleep 3
  docker exec -i "$name" pg_restore -U "$DB_USER" -d "$DB_DJANGO_NAME" --no-owner < "$dump"
  local run=("${COMPOSE[@]}" run --rm -T --no-deps -e SKIP_MIGRATIONS=1 -e DB_HOST="$name" django python manage.py)
  "${run[@]}" migrate --check >/dev/null || die "La sauvegarde $dump n'est pas à jour des migrations."
  "${run[@]}" shell -c "from members.models import Person; from warehouse.models import Order; from bank.models import Operation; from memberships.models import Membership; print('Personnes', Person.objects.count(), '| adhésions', Membership.objects.count(), '| réservations', Order.objects.count(), '| opérations', Operation.objects.count())"
  green "Sauvegarde restaurable : $dump"
}

# ------------------------------------------------------------- Scripts serveur
run_scripts() {
  if [ "${DEBUG:-0}" = "1" ]; then info "Mode debug : outils de surveillance non lancés."; return 0; fi
  python3 "utils/docker-logs.py" > /dev/null 2>&1 & echo $! >> "$PID_FILE"
  python3 "security/main.py" > /dev/null 2>&1 & echo $! >> "$PID_FILE"
  info "Outils de surveillance lancés."
}

stop_scripts() {
  [ -f "$PID_FILE" ] || return 0
  while read -r pid; do kill "$pid" 2>/dev/null || true; done < "$PID_FILE"
  rm -f "$PID_FILE"
}

# ------------------------------------------------------------------ Vérifications
app_responds() { "${COMPOSE[@]}" exec -T django curl -fsS -m 10 http://localhost:8000/sante/ >/dev/null 2>&1; }

# Le site tel que le voient les visiteurs (nginx compris).
public_responds() {
  if [ "${NGINX_CONF_FILE:-conf.d}" = "conf_ssl.d" ]; then
    curl -fsS -k -m 15 --resolve "$SITE_DOMAIN:443:127.0.0.1" "https://$SITE_DOMAIN/sante/" >/dev/null 2>&1
  else
    curl -fsS -m 15 http://127.0.0.1/sante/ >/dev/null 2>&1
  fi
}

wait_healthy() {
  for _ in $(seq 1 40); do
    app_responds && public_responds && return 0
    sleep 3
  done
  return 1
}

health_check() {
  info "Vérification du site…"
  if wait_healthy; then green "Le site répond."; return 0; fi
  "${COMPOSE[@]}" logs --tail 80 django nginx
  return 1
}

# La configuration nginx est montée depuis le dépôt : un « up » ne la relit pas.
reload_nginx() {
  if "${COMPOSE[@]}" exec -T nginx nginx -t >/dev/null 2>&1; then
    "${COMPOSE[@]}" exec -T nginx nginx -s reload >/dev/null 2>&1 || true
  else
    alert "Configuration nginx invalide" "La nouvelle configuration nginx est refusée par « nginx -t » : l'ancienne reste en service. Voir ./run.sh logs nginx"
  fi
}

needs_upgrade() {
  ! manage baseline_migrations --status >/dev/null 2>&1
}

check_iso() {
  # Le serveur doit rester identique au dépôt : aucune modification locale du code.
  local changes
  changes=$(git status --porcelain --untracked-files=no)
  [ -z "$changes" ] || die "Modifications locales sur le serveur (à reporter dans git) :
$changes"
}

# ------------------------------------------------------------------ Commandes
cmd_deploy() {
  lock
  check_iso
  local previous
  previous=$(git rev-parse HEAD)
  backup_db
  if [ "${1:-}" != "--no-pull" ]; then
    info "Récupération du code (branche $(git rev-parse --abbrev-ref HEAD))…"
    git pull --ff-only
  fi
  local current failures_file="$LOG_DIR/deploy.failures" failures
  current=$(git rev-parse HEAD)
  info "Construction de l'image ($(git log -1 --format='%h %s'))…"
  if ! "${COMPOSE[@]}" build django; then
    # Souvent un incident réseau passager : on revient au code en service et on réessaiera.
    git reset --hard "$previous" >/dev/null
    failures=$(( $(cat "$failures_file" 2>/dev/null || echo 0) + 1 ))
    echo "$failures" > "$failures_file"
    if [ "$failures" -eq 3 ]; then
      alert "Déploiement impossible" "La construction de la version $(git rev-parse --short "$current") échoue depuis 3 essais (voir logs/deploy.log). Le site reste sur la version $(git rev-parse --short "$previous")."
    fi
    die "Construction impossible (essai n°$failures) : la version en service est conservée, nouvel essai au prochain passage."
  fi
  rm -f "$failures_file"
  if needs_upgrade; then
    git reset --hard "$previous" >/dev/null
    die "La base doit d'abord être mise à niveau : lancez ./run.sh upgrade (une seule fois)."
  fi
  stop_scripts
  "${COMPOSE[@]}" up -d --remove-orphans
  reload_nginx
  if health_check; then
    git rev-parse HEAD > "$DEPLOYED_FILE"
    docker image prune -f >/dev/null 2>&1 || true
    green "Déploiement terminé : $(git log -1 --format='%h %s')"
    return 0
  fi
  if [ "$current" != "$previous" ]; then
    red "Le site ne répond pas : retour automatique à la version précédente ($previous)."
    git reset --hard "$previous" >/dev/null
    "${COMPOSE[@]}" build django && "${COMPOSE[@]}" up -d --remove-orphans
    reload_nginx
    if wait_healthy; then
      git rev-parse HEAD > "$DEPLOYED_FILE"
      alert "Déploiement annulé" "La version $(git rev-parse --short "$current") ne démarrait pas : le site est revenu automatiquement à $(git rev-parse --short "$previous"). Sauvegarde faite avant : $LAST_BACKUP"
      die "Déploiement annulé, version précédente rétablie."
    fi
  fi
  alert "Site en panne après déploiement" "Le site ne répond plus après le déploiement de $(git rev-parse --short HEAD). Sauvegarde : $LAST_BACKUP"
  die "Le site ne répond pas. Retour arrière manuel : voir DEPLOIEMENT.md."
}

cmd_autodeploy() {
  git fetch --quiet origin "$DEPLOY_BRANCH"
  # On compare à la version réellement en service (pas seulement au code récupéré).
  local deployed
  deployed=$(cat "$DEPLOYED_FILE" 2>/dev/null || git rev-parse HEAD)
  [ "$deployed" = "$(git rev-parse "origin/$DEPLOY_BRANCH")" ] && return 0
  info "Nouvelle version sur origin/$DEPLOY_BRANCH : déploiement."
  cmd_deploy
}

cmd_watchdog() {
  lock try || exit 0  # une opération (déploiement, sauvegarde…) est en cours
  local counter="$LOG_DIR/watchdog.failures" failures
  if public_responds; then rm -f "$counter"; return 0; fi
  failures=$(( $(cat "$counter" 2>/dev/null || echo 0) + 1 ))
  echo "$failures" > "$counter"
  red "Le site ne répond pas (échec n°$failures)."
  [ "$failures" -ge 2 ] || return 0
  info "Redémarrage automatique…"
  "${COMPOSE[@]}" up -d --remove-orphans
  "${COMPOSE[@]}" restart django nginx
  if wait_healthy; then
    rm -f "$counter"
    alert "Site redémarré automatiquement" "Le site ne répondait plus depuis environ $((failures * 5)) minutes : il a été redémarré et répond de nouveau."
  elif [ "$failures" -eq 2 ] || [ $((failures % 12)) -eq 0 ]; then
    alert "Site en panne" "Le site ne répond plus malgré un redémarrage automatique. Journaux : ./run.sh logs"
  fi
}

cmd_maintenance() {
  lock
  info "Maintenance hebdomadaire"
  in_django clearsessions || true
  docker image prune -f >/dev/null 2>&1 || true
  docker builder prune -f --filter until=168h >/dev/null 2>&1 || true
  local log
  for log in "$LOG_DIR"/*.log; do
    [ -f "$log" ] && tail -n 5000 "$log" > "$log.tmp" && mv "$log.tmp" "$log"
  done
  # Certificat HTTPS : renouvelé par certbot, on vérifie qu'il l'est vraiment.
  if [ "${NGINX_CONF_FILE:-conf.d}" = "conf_ssl.d" ]; then
    local end days
    end=$(echo | openssl s_client -connect 127.0.0.1:443 -servername "$SITE_DOMAIN" 2>/dev/null | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2 || true)
    if [ -n "$end" ]; then
      days=$(( ($(date -d "$end" +%s) - $(date +%s)) / 86400 ))
      info "Certificat HTTPS : expire dans $days jours."
      [ "$days" -ge 14 ] || alert "Certificat HTTPS bientôt expiré" "Le certificat de $SITE_DOMAIN expire dans $days jours et n'a pas été renouvelé : vérifier « sudo certbot renew »."
    fi
  fi
  local usage
  usage=$(df --output=pcent / | tail -1 | tr -dc '0-9')
  info "Disque : ${usage}% utilisé."
  [ "$usage" -lt 85 ] || alert "Disque presque plein" "Le disque du serveur est rempli à ${usage}%."
  green "Maintenance terminée."
}

cmd_cron() {
  local tmp
  tmp=$(mktemp)
  crontab -l 2>/dev/null | sed '/# >>> magellans-site/,/# <<< magellans-site/d' > "$tmp" || true
  cat >> "$tmp" <<EOF
# >>> magellans-site — géré par « ./run.sh cron » (heures UTC) >>>
MAILTO=""
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
*/5 * * * *  cd $ROOT && ./run.sh watchdog >> $LOG_DIR/watchdog.log 2>&1
*/10 * * * * cd $ROOT && ./run.sh autodeploy >> $LOG_DIR/deploy.log 2>&1
15 1 * * *   cd $ROOT && ./run.sh backup >> $LOG_DIR/backup.log 2>&1
45 1 * * 0   cd $ROOT && ./run.sh backup --media >> $LOG_DIR/backup.log 2>&1
30 2 1 * *   cd $ROOT && ./run.sh check-backup >> $LOG_DIR/backup.log 2>&1
20 */6 * * * cd $ROOT && ./run.sh sync >> $LOG_DIR/sync.log 2>&1
30 3 * * 1   cd $ROOT && ./run.sh maintenance >> $LOG_DIR/maintenance.log 2>&1
# <<< magellans-site <<<
EOF
  crontab "$tmp"
  rm -f "$tmp"
  green "Tâches automatiques installées :"
  crontab -l | sed -n '/# >>> magellans-site/,/# <<< magellans-site/p'
}

move_legacy_media() {
  # Ancien emplacement des fichiers envoyés : app/assets/media → app/media.
  # (Docker crée app/media, vide, dès qu'un conteneur démarre : on fusionne sans rien écraser.)
  [ -d app/assets/media ] || return 0
  info "Déplacement des médias : app/assets/media → app/media"
  if [ ! -d app/media ] || [ -z "$(ls -A app/media)" ]; then
    rmdir app/media 2>/dev/null || true
    mv app/assets/media app/media
  else
    cp -a -n app/assets/media/. app/media/
    mv app/assets/media "$BACKUP_DIR/medias-ancien-emplacement-$(date +%Y%m%d-%H%M%S)"
  fi
  rmdir app/assets 2>/dev/null || true
  green "Médias en place : $(find app/media -type f | wc -l) fichiers dans app/media."
}

cmd_upgrade() {
  # Mise à niveau unique de l'ancien site (faite le 7 octobre 2026). Conservée pour mémoire.
  lock
  echo "======================================================================"
  echo " Mise à niveau vers la refonte 2026 du site"
  echo " 1. sauvegarde vérifiée de la base et des fichiers"
  echo " 2. alignement de l'historique des migrations (aucune donnée modifiée)"
  echo " 3. migrations additives (nouvelles tables / colonnes uniquement)"
  echo " 4. mise à l'abri des fichiers privés (justificatifs, dossiers, ressources)"
  echo "======================================================================"
  confirm "Continuer ?" || die "Mise à niveau annulée."
  backup_db
  backup_media
  move_legacy_media
  # Les migrations générées sur l'ancien serveur (non versionnées) sont mises de côté.
  local legacy file
  legacy="$BACKUP_DIR/migrations-ancien-site-$(date +%Y%m%d-%H%M%S)"
  for file in $(git ls-files --others --exclude-standard -- 'app/*/migrations/*.py'); do
    mkdir -p "$legacy/$(dirname "$file")"
    mv "$file" "$legacy/$file"
  done
  info "Construction de la nouvelle image…"
  "${COMPOSE[@]}" build django
  stop_scripts
  "${COMPOSE[@]}" stop django nginx 2>/dev/null || true
  info "Diagnostic de l'historique des migrations (aucune modification)…"
  manage baseline_migrations
  if needs_upgrade; then
    manage baseline_migrations --apply
  fi
  info "Application des migrations…"
  manage migrate --noinput
  manage createcachetable
  info "Mise à l'abri des fichiers privés…"
  manage secure_private_media --apply
  "${COMPOSE[@]}" up -d --remove-orphans
  health_check || die "Le site ne répond pas : voir les journaux ci-dessus et DEPLOIEMENT.md."
  git rev-parse HEAD > "$DEPLOYED_FILE"
  info "Synchronisation des adhésions HelloAsso (sans e-mails)…"
  in_django helloasso_sync --all || red "Synchronisation impossible : à relancer avec ./run.sh sync"
  green "Mise à niveau terminée. Sauvegarde de sécurité : $LAST_BACKUP"
}

case "${1:-help}" in
  deploy|update) cmd_deploy "${2:-}" ;;
  autodeploy) lock try || exit 0; exec 9>&-; cmd_autodeploy ;;
  upgrade) cmd_upgrade ;;
  backup) lock; backup_db; [ "${2:-}" = "--media" ] && backup_media; true ;;
  check-backup) lock; cmd_check_backup "${2:-}" ;;
  restore) lock; restore_db "${2:-}" ;;
  cron) cmd_cron ;;
  watchdog) cmd_watchdog ;;
  maintenance) cmd_maintenance ;;
  sync) in_django helloasso_sync "${@:2}" ;;
  up|log) "${COMPOSE[@]}" up -d --remove-orphans; [ "$1" = "log" ] && "${COMPOSE[@]}" logs -f; true ;;
  down) stop_scripts; "${COMPOSE[@]}" down ;;
  restart) "${COMPOSE[@]}" restart django nginx ;;
  status)
    "${COMPOSE[@]}" ps
    git log -1 --format='Code : %h %s (%cr)'
    echo "En service : $(git log -1 --format='%h %s' "$(cat "$DEPLOYED_FILE" 2>/dev/null || echo HEAD)")" ;;
  logs) "${COMPOSE[@]}" logs -f --tail 200 "${2:-django}" ;;
  shell|in) "${COMPOSE[@]}" exec django sh ;;
  python) "${COMPOSE[@]}" exec django python manage.py shell ;;
  manage) shift; in_django "$@" ;;
  runscripts) run_scripts ;;
  stopscripts) stop_scripts ;;
  gitupdate)
    git checkout dev && git push
    git checkout production && git merge --ff-only dev && git push
    git checkout main && git merge --no-edit dev && git push
    git checkout dev ;;
  help|*) sed -n '3,25p' "$0" ;;
esac
