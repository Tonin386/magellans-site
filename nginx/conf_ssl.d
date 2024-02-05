#Config for the main website
server {
    listen 80;
    listen [::]:80;
    server_name magellans.fr;

    return 301 https://magellans.fr;
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name magellans.fr;

    ssl_certificate /app/ssl/fullchain.pem;
    ssl_certificate_key /app/ssl/privkey.pem;

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

    location /ws/ {
        add_header X-debug-message "The /ws/ location was served from the ascend load balancer" always;
        proxy_pass http://django:8000;

        proxy_redirect off;
        proxy_http_version 1.1;

        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}

#Config for every mail related service
server {
    listen 80;
    listen [::]:80;
    server_name mail.magellans.fr;

    return 301 https://mail.magellans.fr;
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name mail.magellans.fr;

    ssl_certificate /app/ssl/fullchain.pem;
    ssl_certificate_key /app/ssl/privkey.pem;

    location / {
        proxy_pass http://roundcube:80;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Server $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        access_log /var/log/nginx/access_backend.log;
        error_log /var/log/nginx/error_backend.log;
    }
}

server {
    listen 587;
    server_name mail.magellans.fr;

    location / {
        proxy_pass http://mail-server:587;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Additional configuration for your SMTP server if needed...
}

server {
    listen 993;
    server_name mail.magellans.fr;

    location / {
        proxy_pass http://mail-server:993;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Additional configuration for your IMAP server if needed...
}