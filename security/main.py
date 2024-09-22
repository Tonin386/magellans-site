from datetime import datetime, timedelta
from ListManager import ListManager
from IPChecker import IPChecker
from colorama import init, Fore
from dotenv import load_dotenv
from collections import deque
import subprocess
import threading
import requests
import json
import time
import re
import os

init()
load_dotenv()

default_print = print

def print_reset(* args, **kwargs):
    end = kwargs.pop('end', '\n')
    default_print(*args, **kwargs, end=end)
    default_print(Fore.RESET, end="")

print = print_reset

INTERFACE = "ens3"
CHECKER = IPChecker()

AUTHORIZED_DOMAINS = ['ovh.com', 'ovh.fr', 'ovh.net', 'magellans.fr']
COMMON_PORTS = ['80', '443', '21', '22', '25', '53', '67', '68', '110', '143', '23', '587', '465', '993']
CONFIDENCE_THRESHHOLD = 65

SOURCE = os.getenv("SOURCE_IP")
WEBHOOK = os.getenv("WEBHOOK_SECURITY_LOGS")

class IP():
    def __init__(self, ip, port_src, port_dst):
        self.ip = ip
        self.port_src = port_src
        self.port_dst = port_dst

    def str_discord(self):
        return self.ip + "(:" + self.port_src + " > :"+ self.port_dst +")"
    
    def __str__(self):
        return f"{self.ip}{Fore.LIGHTMAGENTA_EX}(:{self.port_src} > :{self.port_dst}){Fore.RESET}"
    
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, IP):
            raise TypeError("Can only compare IP with another IP.")
        return self.ip == value.ip and self.port_dst == value.port_dst and self.port_src == value.port_src

def log_in_discord(message, extraData=None):
    payload = {'timestamp': datetime.now().isoformat() + 'Z'}
    headers = {'Content-type': 'application/json'}

    if extraData:
        message += "\n"
        message += "==================================================\n"
        message += f"*\tINFOS SUR {extraData['ip']}\n"
        message += f"*\tORIGINE : {extraData['countryName']} | {extraData['domain']}\n"
        message += f"*\tDANGER : {extraData['abuseConfidenceScore']}%\tTOTAL REPORTS : {extraData['totalReports']}\n"
        message += "==================================================\n"

    payload['content'] = "```" + message + "```"
    
    try:
        response = requests.post(WEBHOOK, json=payload, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de l'envoi au webhook : {e}")
        print(f"Payload envoyé : {json.dumps(payload, indent=4)}")

def extract_ip_addresses(text):
    port_pattern = r'((?:\d{1,3}\.){3}\d{1,3})\.(\d+) > ((?:\d{1,3}\.){3}\d{1,3})\.(\d+)'
    ip_pattern = r'((?:\d{1,3}\.){3}\d{1,3}) > ((?:\d{1,3}\.){3}\d{1,3})'
    port_matches = re.findall(port_pattern, text)
    ip_matches = re.findall(ip_pattern, text)
    if len(port_matches) >= 1:
        return port_matches[0][0], port_matches[0][1], port_matches[0][2], port_matches[0][3]
    elif len(ip_matches) >= 1:
        return ip_matches[0][0], None, ip_matches[0][1], None

    return None, None, None, None

def capture_output(process):
    last_ips = deque(maxlen=10000000)
    for line in iter(process.stdout.readline, b''):
        str_line = line.decode('utf-8')

        ip_src, port_src, ip_dest, port_dest = extract_ip_addresses(str_line)
        
        if not ip_src:
            continue

        if not port_src:
            port_src = "?"

        if not port_dest:
            port_dest = "?"
            
        ip = IP(ip_src, port_src, port_dest)
        
        manager = ListManager(["whitelist", "blacklist", "ignorelist"])
        manager.saveIP(ip)

        if not ip.ip:
            continue

        if (ip.ip == SOURCE or ip.ip in manager.getList("ignorelist") or ip in last_ips) and (ip.port_dst not in COMMON_PORTS or ip in list(last_ips)[-100:]):
            continue

        last_ips.append(ip)

        if ip.ip in manager.getList("whitelist"):
            print(f"{Fore.LIGHTGREEN_EX}{str(ip)}{Fore.LIGHTGREEN_EX} est présente dans la whitelist.")
            log_in_discord(ip.str_discord() + " est présente dans la whitelist.")
            continue

        if ip.ip in manager.getList("blacklist"):
            print(f"{Fore.LIGHTRED_EX}{str(ip)}{Fore.LIGHTRED_EX} est présente dans la blacklist.")
            log_in_discord(ip.str_discord() + " est présente dans la blacklist.")
            continue

        print(f"{Fore.LIGHTBLUE_EX}Nouvelle IP détectée : {str(ip)}{Fore.LIGHTBLUE_EX}.")
        message = "Nouvelle IP détectée : " + ip.str_discord()
        infos = CHECKER.checkIP(ip.ip)
        if 'errors' in infos.keys():
            log_in_discord(infos["errors"] + "\n" + "Mise en pause du service. Reprise demain à 00h00.")
            waiting_time = (datetime.combine(datetime.now().date() + timedelta(days=1), datetime.min.time()) - datetime.now()).total_seconds()
            time.sleep(waiting_time)
            continue

        infos['ip'] = ip.str_discord()
        log_in_discord(message, infos)
        if infos['abuseConfidenceScore'] >= CONFIDENCE_THRESHHOLD and not infos['domain'] in AUTHORIZED_DOMAINS:
            manager.banIP(ip.ip)
            log_in_discord(ip.str_discord() + " a été bannie.")
            continue

        elif infos['totalReports'] < 100 and infos['abuseConfidenceScore'] > 0 and not infos['domain'] in AUTHORIZED_DOMAINS:
            print(f"{Fore.YELLOW}{ip.ip} est incertaine. Aucune action effectuée.")
            log_in_discord(ip.str_discord() + " est incertaine. Aucune action effectuée.")
            continue
        
        print(f"{Fore.GREEN}L'adresse IP n'est pas dangereuse. Ajout à la whitelist.")
        log_in_discord("L'adresse IP n'est pas dangeureuse. Ajout à la whitelist.")
        manager.addIP(ip.ip, "whitelist")

def execute_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    output_thread = threading.Thread(target=capture_output, args=(process,))
    output_thread.start()
    process.wait()
    output_thread.join()

def main():
    ignoreList = ListManager(["whitelist", "blacklist", "ignorelist"]).getList("ignorelist")

    tcp_command = f'sudo tcpdump -i {INTERFACE} dst host {SOURCE} and not \\(host { " or host ".join(ignoreList)}\\) -n -nnn -t'

    execute_command(tcp_command)

if __name__ == "__main__":
    main()