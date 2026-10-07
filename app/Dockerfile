# syntax=docker/dockerfile:1.7
# Image du site magellans.fr — construite en deux étapes :
# 1. Node : compilation des fichiers frontend (Vite, Tailwind CSS, icônes) ;
# 2. Python : application Django, sans Node ni outils de compilation.

FROM node:22-bookworm-slim AS assets
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json frontend/
RUN cd frontend && npm ci --no-audit --no-fund
COPY . .
RUN cd frontend && npm run build


FROM python:3.14-slim-bookworm AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
# Bibliothèques nécessaires à WeasyPrint (contrats PDF) et à Pillow.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 libjpeg62-turbo libwebp7 \
        fonts-dejavu-core curl postgresql-client \
    && rm -rf /var/lib/apt/lists/*
RUN useradd --create-home --uid 1000 magellans
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
COPY --from=assets /app/frontend/dist /app/frontend/dist
COPY --from=assets /app/static/icons.svg /app/static/icons.svg
RUN SECRET_KEY=collectstatic-only python manage.py collectstatic --noinput --verbosity 0 \
    && chown -R magellans:magellans /app/staticfiles \
    && chmod +x /app/docker-entrypoint.sh
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -fsS http://localhost:8000/sante/ || exit 1
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "magellans.wsgi:application", "-c", "gunicorn.conf.py"]
