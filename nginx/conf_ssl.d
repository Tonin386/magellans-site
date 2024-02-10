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
    listen [::]:443 ssl;
    server_name webmail.magellans.fr;

    ssl_certificate /etc/letsencrypt/live/magellans.fr/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/magellans.fr/privkey.pem;

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

# worker_processes auto;
# mail {
#     server_name mail.magellans.fr;
#     auth_http   mail-server/cgi-bin/nginxauth.cgi;

#     proxy_pass_error_message on;

#     ssl                 on;
#     ssl_certificate /etc/letsencrypt/live/magellans.fr/fullchain.pem;
#     ssl_certificate_key /etc/letsencrypt/live/magellans.fr/privkey.pem;
#     ssl_protocols       TLSv1 TLSv1.1 TLSv1.2;
#     ssl_ciphers         HIGH:!aNULL:!MD5;
#     ssl_session_cache   shared:SSL:10m;
#     ssl_session_timeout 10m;

#     server {
#         listen     587;
#         protocol   smtp;
#         smtp_auth  login plain cram-md5;
#     }

#     server {
#         listen   993;
#         protocol imap;
#     }
# }