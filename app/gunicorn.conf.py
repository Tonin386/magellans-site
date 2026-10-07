"""Configuration de gunicorn (serveur d'application en production)."""

import os

bind = "0.0.0.0:8000"
worker_class = "gthread"
workers = int(os.getenv("GUNICORN_WORKERS", "3"))
threads = int(os.getenv("GUNICORN_THREADS", "4"))
timeout = 90  # génération de PDF, appels à l'API HelloAsso
graceful_timeout = 30
max_requests = 1000
max_requests_jitter = 100
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")
# Le serveur n'est joignable que par nginx, sur le réseau Docker interne.
forwarded_allow_ips = "*"
