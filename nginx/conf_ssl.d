# Configuration de production (HTTPS, certificats Let's Encrypt).

# Noms d'hôte inconnus (scans par adresse IP…) : connexion refusée.
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    return 444;
}

server {
    listen 443 ssl default_server;
    listen [::]:443 ssl default_server;
    ssl_reject_handshake on;
}

# Redirections HTTP → HTTPS (sauf les jetons de validation Let's Encrypt, méthode HTTP-01)
server {
    listen 80;
    listen [::]:80;
    server_name magellans.fr www.magellans.fr;
    location /.well-known/acme-challenge/ { root /var/www/certbot; }
    location / { return 301 https://magellans.fr$request_uri; }
}

# www → domaine principal
server {
    listen 443 ssl;
    listen [::]:443 ssl;
    http2 on;
    server_name www.magellans.fr;
    ssl_certificate /etc/letsencrypt/live/magellans.fr/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/magellans.fr/privkey.pem;
    return 301 https://magellans.fr$request_uri;
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    http2 on;
    server_name magellans.fr;

    ssl_certificate /etc/letsencrypt/live/magellans.fr/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/magellans.fr/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;
    # HSTS : ajouté par Django pour les pages, et ci-dessous pour les fichiers servis par nginx.

    # Médias publics (affiches, photos du matériel, équipe…)
    location /media/ {
        alias /srv/media/;
        expires 30d;
        add_header Strict-Transport-Security "max-age=31536000" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Content-Security-Policy "default-src 'none'; img-src 'self'; media-src 'self'; style-src 'unsafe-inline'; sandbox" always;
    }

    # Fichiers privés : uniquement servis après vérification des droits par Django (X-Accel-Redirect).
    location /_protected/ {
        internal;
        alias /srv/private/;
        add_header Strict-Transport-Security "max-age=31536000" always;
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
