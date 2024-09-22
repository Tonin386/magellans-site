from ListManager import ListManager
from IPChecker import IPChecker
import re

CHECKER = IPChecker()

def is_IP(str_check):
    pattern = r'^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    return re.match(pattern, str_check) is not None

def dialog_terminal():
    while True:        
        user_input = input(">")
        args = user_input.split(" ")

        MANAGER = ListManager(["whitelist", "blacklist", "ignorelist"])
        if args[0] == "force-ban":
            ip = args[1]
            if not is_IP(ip):
                print("L'adresse IP rentrée n'est pas valide.")
                continue

            MANAGER.removeIP(ip, "whitelist")
            MANAGER.banIP(ip)
            continue
    
        if args[0] == "force-allow":
            ip = args[1]
            if not is_IP(ip):
                print("L'adresse IP rentrée n'est pas valide.")
                continue

            print("L'IP a été ajoutée à la whitelist.") if MANAGER.addIP(ip, 'whitelist') else print("Impossible d'ajouter l'IP à la whitelist")
            continue

        if args[0] == "report":
            ip = args[1]
            if not is_IP(ip):
                print("L'adresse IP rentrée n'est pas valide.")
                continue

            message = "".join(args[2:])

            CHECKER.reportIP(ip, message)
            continue

        if args[0] == "check":
            ip = args[1]
            if not is_IP(ip):
                print("L'adresse IP rentrée n'est pas valide.")
                continue

            listName, ip_info = MANAGER.getIP(ip)
            print(f"{ip} est présente dans {listName}.")
            if ip_info:
                print(f"{'|'.join([str(x) for x in sorted([int(x) for x in ip_info['ports_src']])])} > {'|'.join([str(x) for x in sorted([int(x) for x in ip_info['ports_dst']])])}")
            continue

        if args[0] == "count":
            listName = args[1]
            print(f"'{listName}' a {MANAGER.countList(listName)} IPs.")
            continue

        if args[0] == "exit":
            return 0

def main():
    dialog_terminal()

if __name__ == "__main__":
    main()