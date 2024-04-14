#Config for the main website
server {
    listen 80;
    listen [::]:80;
    server_name magellans.fr;

    return 301 https://magellans.fr;
}

server {
    listen 80;
    listen [::]:80;
    server_name mail.magellans.fr;

    return 301 https://magellans.fr;
}

server {
    listen 443 ssl;
    listen [::]:443 ssl http2;
    server_name autodiscover.magellans.fr;

    ssl_certificate /etc/letsencrypt/live/magellans.fr/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/magellans.fr/privkey.pem;
}

server {
    listen 443 ssl;
    listen [::]:443 ssl http2;
    server_name magellans.fr;

    client_max_body_size 25M;

    ssl_certificate /etc/letsencrypt/live/magellans.fr/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/magellans.fr/privkey.pem;

    log_format magellans_format '$remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent"';

    location /static/ {
        alias /app/staticfiles/;
    }

    location /media/ {
        alias /app/staticfiles/media/;
    }

    location / {
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Server $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        access_log /var/log/nginx/access.log magellans_format debug;
        error_log /var/log/nginx/error.log magellans-format error;

        access_log /dev/stdout magellans_format debug;
        error_log /dev/stderr magellans-format error;

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
    server_name webmail.magellans.fr;

    return 301 https://webmail.magellans.fr;
}

server {
    listen 443 ssl;
    listen [::]:443 ssl http2;
    server_name webmail.magellans.fr;

    ssl_certificate /etc/letsencrypt/live/magellans.fr/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/magellans.fr/privkey.pem;
    
    log_format magellans_format '$remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent"';

    location / {
        proxy_pass http://roundcube:80;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Server $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        access_log /var/log/nginx/access.log magellans_format debug;
        error_log /var/log/nginx/error.log magellans-format error;

        access_log /dev/stdout magellans_format debug;
        error_log /dev/stderr magellans-format error;
    }
}