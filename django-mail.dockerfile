FROM ubuntu:latest

RUN apt-get update && apt-get upgrade -y && \
    apt-get install postfix dovecot-imapd dovecot-pop3d systemctl -y

RUN systemctl restart postfix && \
    systemctl restart dovecot

CMD ["/bin/bash"]