# Configuration de développement (HTTP seulement).
server {
    listen 80;
    listen [::]:80;
    server_name localhost;

    # Médias publics (affiches, photos du matériel, équipe…)
    location /media/ {
        alias /srv/media/;
        expires 30d;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Content-Security-Policy "default-src 'none'; img-src 'self'; media-src 'self'; style-src 'unsafe-inline'; sandbox" always;
    }

    # Fichiers privés : uniquement servis après vérification des droits par Django (X-Accel-Redirect).
    location /_protected/ {
        internal;
        alias /srv/private/;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Content-Security-Policy "default-src 'none'; img-src 'self'; style-src 'unsafe-inline'; sandbox" always;
        add_header Cache-Control "private, no-store" always;
    }

    location ~ ^/(connexion|inscription|mot-de-passe|contact)/ {
        limit_req zone=forms burst=10 nodelay;
        proxy_pass http://django:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_read_timeout 90s;
    }

    location / {
        proxy_pass http://django:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_read_timeout 90s;
    }
}
