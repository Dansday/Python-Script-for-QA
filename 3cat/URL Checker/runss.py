import requests
import gzip
from bs4 import BeautifulSoup
import time
import random
import csv
import os
import signal
import sys
import certifi
import logging
from typing import Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.117 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36"
]

crawled_urls = set()

def get_status_code(url: str) -> Tuple[Optional[int], Optional[str]]:
    headers = {'User-Agent': random.choice(user_agents)}
    try:
        response = requests.get(url, headers=headers, timeout=30, allow_redirects=False, verify=certifi.where())
        time.sleep(0.5)
        if response.status_code in [301, 302]:
            redirected_url = response.headers.get('Location')
            return response.status_code, redirected_url
        return response.status_code, url
    except requests.exceptions.RequestException as err:
        logging.error(f"RequestException error occurred: {err}")
    except requests.exceptions.HTTPError as errh:
        logging.error(f"HTTPError occurred: {errh}")
    except requests.exceptions.ConnectionError as errc:
        logging.error(f"ConnectionError occurred: {errc}")
    except requests.exceptions.Timeout as errt:
        logging.error(f"Timeout error occurred: {errt}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

    return None, None

def process_url(sitemap_url: str, writer: csv.writer):
    status_code, final_url = get_status_code(sitemap_url)
    if status_code is not None:
        logging.info(f"  Status: {status_code}")
        if status_code == 200:
            logging.info(f"  Valid URL")
            writer.writerow([final_url, status_code, "Valid URL"])
        elif status_code in [301, 302]:
            logging.info(f"  Redirect URL")
            writer.writerow([sitemap_url, status_code, f"Redirect to {final_url}"])
        else:
            logging.info(f"  Invalid URL")
            writer.writerow([sitemap_url, status_code, "Invalid URL"])
    else:
        logging.info(f"  Need Manual Check")
        writer.writerow([sitemap_url, "N/A", "Need Manual Check"])

def crawl_sitemap(url: str, writer: csv.writer):
    headers = {'User-Agent': random.choice(user_agents)}
    response = requests.get(url, headers=headers, stream=True, verify=certifi.where())

    if 'Content-Disposition' in response.headers.keys():
        decompressed_content = gzip.decompress(response.content)
        soup = BeautifulSoup(decompressed_content, 'xml')
    else:
        soup = BeautifulSoup(response.content, 'xml')
    urls = soup.find_all('loc')

    for url in urls:
        sitemap_url = url.get_text()
        if sitemap_url in crawled_urls:
            logging.info(f"Skipping URL (already crawled): {sitemap_url}")
            continue
        else:
            crawled_urls.add(sitemap_url)

        logging.info(f"Crawling URL: {sitemap_url}")
        process_url(sitemap_url, writer)

def main():
    csv_filename = input("Enter the CSV filename to save/load data: ")
    csv_exists = os.path.exists(csv_filename)

    with open(csv_filename, 'a', newline='') as csv_file:
        fieldnames = ['URL', 'URL Status Code', 'Information']
        writer = csv.writer(csv_file)
        if not csv_exists:
            writer.writerow(fieldnames)

        def signal_handler(signal, frame):
            logging.info("\nScript interrupted. Saving data and exiting...")
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)

        if csv_exists:
            logging.info(f"Resuming from the last crawled URL in '{csv_filename}'...")
            with open(csv_filename, 'r') as existing_csv_file:
                reader = csv.DictReader(existing_csv_file)
                for row in reader:
                    crawled_urls.add(row['URL'])

        sitemap_url = input("Enter the sitemap: ")
        sitemap_host = sitemap_url.split('/sitemap_index.xml')[0]
        crawl_sitemap(sitemap_url, writer)

        list_filename = 'list.txt'
        if os.path.exists(list_filename):
            with open(list_filename, 'r') as list_file:
                for line in list_file:
                    url = line.strip()

                    if not url.endswith('/'):
                        url += '/'
                    full_url = f"{sitemap_host.rstrip('/')}/{url}"
                    if full_url in crawled_urls:
                        logging.info(f"Skipping URL (already crawled): {full_url}")
                        continue
                    else:
                        crawled_urls.add(full_url)

                    logging.info(f"Crawling URL: {full_url}")
                    process_url(full_url, writer)

if __name__ == "__main__":
    main()
