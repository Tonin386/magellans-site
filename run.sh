#!/bin/bash

PID_FILE="pids.txt"

run_scripts() {
  python3 "utils/docker-logs.py" > /dev/null &
  echo $! >> "$PID_FILE"
  python3 "security/main.py" > /dev/null &
  echo $! >> "$PID_FILE"
}

stop_scripts() {
  if [[ -f "$PID_FILE" ]]; then
    while read -r pid; do
      if kill -0 "$pid" 2>/dev/null; then
        kill "$pid"
        echo "Arrêt du processus $pid"
      else
        echo "Processus $pid introuvable."
      fi
    done < "$PID_FILE"
    rm "$PID_FILE"
  else
    echo "Aucun PID trouvé."
  fi
}

if [ "$#" -ne 1 ]; then
  echo "Wrong usage."
  exit 1
fi

if [ "$1" = "up" ]; then
  stop_scripts &
  echo "Starting my django app."
  docker compose --env-file app/.env up -d
  run_scripts &
elif [ "$1" = "log" ]; then
  stop_scripts &
  run_scripts &
  docker compose --env-file app/.env up
elif [ "$1" = "down" ]; then
  stop_scripts &
  docker compose --env-file app/.env down
elif [ "$1" = "in" ]; then
  stop_scripts &
  docker compose --env-file app/.env up -d
  run_scripts &
  docker exec -it magellans-django sh
elif [ "$1" = "db" ]; then
  stop_scripts &
  docker compose --env-file app/.env up -d
  run_scripts &
  docker exec -it magellans-django python manage.py makemigrations
  docker exec -it magellans-django python manage.py migrate
elif [ "$1" = "python" ]; then
  stop_scripts &
  docker compose --env-file app/.env up -d
  run_scripts &
  docker exec -it magellans-django python manage.py shell
elif [ "$1" = "update" ]; then
  git pull
  stop_scripts &
  docker compose --env-file app/.env down
  docker compose --env-file app/.env up -d
  run_scripts &
  docker exec -it magellans-django python manage.py makemigrations
  docker exec -it magellans-django python manage.py migrate
elif [ "$1" = "gitupdate" ]; then
  git checkout dev
  git push
  git checkout production
  git merge dev
  git push
  git checkout main
  git merge dev
  git push
  git checkout dev
else
  echo "Invalid argument."
  exit 1
fi