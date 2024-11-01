import requests
import yaml
import random
import time
import uuid

from concurrent.futures import ThreadPoolExecutor, as_completed
from logmagix import Logger, Home
import threading

log = Logger()
home = Home("Configuration", "center", credits="discord.cyberious.xyz").display()

stop_event = threading.Event()

try:
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
        username = config.get("Username") or log.question("Please enter the NGL.link username of the victim: ")
        question = config.get("Question") or log.question("Please enter the NGL.link message: ")
        number = int(config.get("Number") or log.question("Please enter the number of times the message will be sent: "))
        threads = int(config.get("Threads") or log.question("Please enter the amount of threads: "))
        proxyless = config.get("Proxyless", True)
        bypass_block = config.get("BypassBlock", False)
    proxies = []
    if not proxyless:
        with open('proxies.txt', 'r') as f:
            proxies = [line.strip() for line in f if line.strip()]

    home = Home("NGL spammer", "center", credits="discord.cyberious.xyz", adinfo1=f"Loaded Proxies: {len(proxies)}" if not proxyless else "Proxyless Mode Enabled").display()

    base_payload = f"username={username}&question={question}"
    headers = {
        "host": "ngl.link",
        "connection": "keep-alive",
        "sec-ch-ua-platform": "\"Android\"",
        "x-requested-with": "XMLHttpRequest",
        "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
        "accept": "*/*",
        "sec-ch-ua": "\"Chromium\";v=\"130\", \"Google Chrome\";v=\"130\", \"Not?A_Brand\";v=\"99\"",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "sec-ch-ua-mobile": "?1",
        "origin": "https://ngl.link",
        "sec-fetch-site": "same-origin",
        "sec-fetch-mode": "cors",
        "sec-fetch-dest": "empty",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    success_count = 0

    def get_proxy_dict():
        return None if proxyless else {"http": f"http://{random.choice(proxies)}", "https": f"http://{random.choice(proxies)}"}

    def send_request():
        global success_count
        payload = base_payload + (f"&deviceId={str(uuid.uuid4())}" if bypass_block else "")

        if stop_event.is_set():
            return False
        try:
            response = requests.post("https://ngl.link/api/submit", data=payload, headers=headers, proxies=get_proxy_dict(), timeout=5)
            if response.status_code == 200:
                resp = response.json()
                log.success(f"Successfully sent message. Id: {resp['questionId']}, count: {success_count}")
                success_count += 1
            elif response.status_code == 400:
                log.failure(f"Failed to send message. Check username and message length. Status code: {response.status_code}")
                return False
            elif response.status_code == 404:
                log.failure(f"Failed to send message. {response.text}")
                return False
            elif response.status_code == 429:
                if not proxyless:
                    log.warning(f"Rate limit reached. Retrying with another proxy...")
                else:
                    log.warning("Rate limit reached.")
                    time.sleep(1)
                return None
            else:
                log.failure(f"Error sending message: {response.text}, {response.status_code}")
                return False
        except Exception as e:
            log.failure(f"Request error: {e}")
        return True

    messages_per_thread = max(1, number // threads)
    remaining_messages = number % threads

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = []
        try:
            for _ in range(threads):
                messages_to_send = messages_per_thread + (1 if remaining_messages > 0 else 0)
                remaining_messages -= 1
                futures.extend([executor.submit(send_request) for _ in range(messages_to_send)])

            for future in as_completed(futures):
                if stop_event.is_set(): 
                    break
                if not future.result():
                    break
        except KeyboardInterrupt:
            log.info("Program interrupted by user. Exiting...")
            stop_event.set()
            executor.shutdown(wait=False, cancel_futures=True)

    log.success(f"Finished sending messages. Total successful sends: {success_count}")
    input()
except KeyboardInterrupt:
    log.info("Program interrupted by user. Exiting...")
    stop_event.set()  
except Exception as e:
    log.failure(f"An error occurred: {e}")