import os
import re
import json
import subprocess
from colorama import Fore

DIR = os.path.dirname(__file__)

default_print = print

def print_reset(* args, **kwargs):
    end = kwargs.pop('end', '\n')
    default_print(*args, **kwargs, end=end)
    default_print(Fore.RESET, end="")

print = print_reset

def is_IP(str_check):
    pattern = r'^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    return re.match(pattern, str_check) is not None

class ListManager():
    def __init__(self, existingLists = None) -> None:
        self.lists = {}

        try:
            with open("ips.json", "r") as f:
                self.ips = json.load(f)
        except:
            self.ips = {}

        for existingList in existingLists:
            json_file = os.path.join(DIR, "lists", f"{existingList}.json")
            if not os.path.exists(json_file):
                self.lists[existingList] = []
            else:
                with open(json_file, 'r') as f:
                    self.lists[existingList] = json.load(f)

    def _saveListToFile(self, listName: str):
        json_file = os.path.join(DIR, "lists", f"{listName}.json")
        with open(json_file, 'w') as f:
            json.dump(self.lists[listName], f)

                    
    def addIP(self, ip: str, listName: str) -> bool:
        if not is_IP(ip):
            print(f"'{ip}' n'est pas une adresse IP valide.")
            return False

        if not listName in self.lists.keys():
            print("Cette liste n'existe pas.")
            return False
        
        if ip in self.lists[listName]:
            print("Cette IP est déjà présente dans la liste.")
            return False
        
        self.lists[listName].append(ip)

        self._saveListToFile(listName)

        return True
    
    def getIP(self, ip: str) -> tuple:
        if not is_IP(ip):
            print(f"'{ip}' n'est pas une adresse IP valide.")
            return []
        
        matchLists = []
        for l in self.lists:
            if ip in self.lists[l]:
                matchLists.append(l)

        ip_info = self.ips.get(ip, None)

        return matchLists, ip_info
    
    def banIP(self, ip: str) -> bool:
        command = f"bash {DIR}/ban.sh {ip}"
        try:
            subprocess.check_output(command, shell=True, text=True)
            self.addIP(ip, "blacklist")
            print(f"{Fore.RED}{ip} bannie.")
        except subprocess.CalledProcessError as e:
            print(f"Impossible d'exécuter la commande. {e}")
            return False
        
        return True
    
    def removeIP(self, ip: str, listName: str) -> bool:
        if not listName in self.getIP(ip)[0]:
            return False
        
        self.lists[listName].remove(ip)
        self._saveListToFile(listName)
        return True
    
    def getList(self, listName) -> list:
        if not listName in self.lists.keys():
            print("Cette liste n'existe pas.")
            return []
        return self.lists[listName]
    
    def countList(self, listName: str) -> int:
        if not listName in self.lists.keys():
            print("Cette liste n'existe pas.")
            return 0
        return len(self.lists[listName])
    
    def saveIP(self, ip: object) -> None:
        if not ip.ip in self.ips.keys():
            self.ips[ip.ip] = {"ports_dst": [], "ports_src": []}

        port_dst = ip.port_dst if ip.port_dst != "?" else 99999
        port_src = ip.port_src if ip.port_src != "?" else 99999
        
        if not port_dst in self.ips[ip.ip]['ports_dst']:
            self.ips[ip.ip]['ports_dst'].append(port_dst)

        if not port_src in self.ips[ip.ip]['ports_src']:
            self.ips[ip.ip]['ports_src'].append(port_src)

        with open("ips.json", "w") as f:
            json.dump(self.ips, f)