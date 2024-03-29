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
else
  echo "Invalid argument."
  exit 1
fi


