from dotenv import load_dotenv
import requests
import json
import os

load_dotenv()

class IPChecker():
    def __init__(self) -> None:
        self._HEADERS = {
            'Accept': 'application/json',
            'Key': os.getenv("API_KEY"),
        }
        self._URL = 'https://api.abuseipdb.com/api/v2/'

    def checkIP(self, ip, verbose=True) -> dict:
        query = {
            'ipAddress': ip,
            'verbose': True
        }

        endpoint = "check"

        response = requests.request(method="GET", url=self._URL + endpoint, headers=self._HEADERS, params=query)
        data = json.loads(response.text).get('data', json.loads(response.text).get('errors'))

        if verbose and 'countryName' in data.keys():
            print("==================================================")
            print(f"*\tINFOS SUR {ip}")
            print(f"*\tORIGINE : {data['countryName']} | {data['domain']}")
            print(f"*\tDANGER : {data['abuseConfidenceScore']}%\tTOTAL REPORTS : {data['totalReports']}")
            print("==================================================")

        return data
    
    def reportIP(self, ip, message, verbose=True) -> dict:
        query = {
            'ip': ip,
            'categories': "14,18,21,15",
            'comment': message
        }

        endpoint = "report"

        response = requests.request(method="POST", url=self._URL + endpoint, headers=self._HEADERS, params=query)
        data = json.loads(response.text)
        print(data)

        if verbose:
            print(f"{ip} a été signalée.")

        return data.get('data', {})