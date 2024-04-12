#!/bin/bash

if [ "$#" -ne 1 ]; then
  echo "Wrong usage."
  exit 1
fi

if [ "$1" = "up" ]; then
  echo "Starting my django app."
  docker compose --env-file app/.env up -d
elif [ "$1" = "log" ]; then
  docker compose --env-file app/.env up
elif [ "$1" = "down" ]; then
  docker compose --env-file app/.env down
elif [ "$1" = "in" ]; then
  docker compose --env-file app/.env up -d
  docker exec -it magellans-django sh
elif [ "$1" = "db" ]; then
  docker compose --env-file app/.env up -d
  docker exec -it magellans-django python manage.py makemigrations
  docker exec -it magellans-django python manage.py migrate
elif [ "$1" = "python" ]; then
  docker compose --env-file app/.env up -d
  docker exec -it magellans-django python manage.py shell
elif [ "$1" = "update" ]; then
  git pull
  docker compose --env-file app/.env down
  docker compose --env-file app/.env up -d
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