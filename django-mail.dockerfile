FROM ubuntu:latest

RUN apt-get update && apt-get upgrade -y && \
    apt-get install postfix dovecot-imapd dovecot-pop3d -y

CMD service postfix start && service dovecot start && tail -f /dev/null