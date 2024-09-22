from dotenv import load_dotenv
from datetime import datetime
import subprocess
import requests
import time
import json
import os

load_dotenv()

def send_to_webhook(webhook_url, payload):
    payload['timestamp'] = datetime.now().isoformat() + 'Z'
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(webhook_url, json=payload, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de l'envoi au webhook : {e}")
        print(f"Payload envoyé : {json.dumps(payload, indent=4)}")

def get_docker_logs(container_name):
    try:
        process = subprocess.Popen(['docker', 'logs', '-f', container_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de la récupération des logs : {e}")
        return None

def main():
    container_name = os.getenv("CONTAINER_NGINX")
    webhook_url = os.getenv("WEBHOOK_NGINX_WEB")

    process = get_docker_logs(container_name)
    if process:
        try:
            while True:
                log_line = process.stdout.readline().decode('utf-8').strip()
                if log_line:
                    payload = {
                        'content': "```" + log_line + "```"
                    }
                    send_to_webhook(webhook_url, payload)
                time.sleep(0.5)
        except KeyboardInterrupt:
            process.terminate()

if __name__ == '__main__':
    main()