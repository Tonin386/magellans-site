server {
    listen 80;
    listen [::]:80;
    server_name magellans.fr;

    location /static/ {
        alias /app/staticfiles/;
    }

    location / {
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Server $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        access_log /var/log/nginx/access_backend.log;
        error_log /var/log/nginx/error_backend.log;
		proxy_pass http://django:8000;
	}
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name magellans.fr;

    ssl_certificate /etc/letsencrypt/live/magellans.fr/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/magellans.fr/privkey.pem;

    location /static/ {
        alias /app/staticfiles/;
    }

    location / {
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Server $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        access_log /var/log/nginx/access_backend.log;
        error_log /var/log/nginx/error_backend.log;
		proxy_pass http://django:8000;
    }
}