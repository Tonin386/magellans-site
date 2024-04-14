server {
    listen 80;
    listen [::]:80 http2;
    server_name localhost;

    client_max_body_size 25M;

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

        access_log /var/log/nginx/access.log;
        error_log /var/log/nginx/error.log;

        access_log /dev/stdout;
        error_log /dev/stderr;

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