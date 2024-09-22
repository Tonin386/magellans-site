sudo iptables -I DOCKER-USER 1 -s "$1" -j DROP
sudo iptables -A INPUT -s "$1" -j DROP
sudo iptables-save
sudo iptables-save > /etc/iptables/rules.v4
sudo ip6tables-save > /etc/iptables/rules.v6