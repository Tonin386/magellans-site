server {
    listen 80;
    listen [::]:80 http2;
    server_name localhost;

    log_format magellans_format '$remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent"';

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