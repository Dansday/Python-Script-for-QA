import requests
import gzip
from bs4 import BeautifulSoup
import time
import random
import csv
import os
import signal
import sys
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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

def get_status_code(url):
    headers = {'User-Agent': random.choice(user_agents)}
    try:
        response = requests.get(url, headers=headers, timeout=30, allow_redirects=False, verify=False)
        time.sleep(0.5)
        if response.status_code == 301 or response.status_code == 302:
            redirected_url = response.headers.get('Location')
            return response.status_code, redirected_url
        return response.status_code, url
    except requests.exceptions.RequestException as err:
        print("RequestException error occurred:", err)
    except requests.exceptions.HTTPError as errh:
        print("HTTPError occurred:", errh)
    except requests.exceptions.ConnectionError as errc:
        print("ConnectionError occurred:", errc)
    except requests.exceptions.Timeout as errt:
        print("Timeout error occurred:", errt)
    except Exception as e:
        print("An unexpected error occurred:", e)

    return None, None

def crawl_sitemap(url, writer):
    valid = "Valid URL"
    invalid = "Invalid URL"
    na = "N/A"
    manual = "Need Manual Check"
    headers = {'User-Agent': random.choice(user_agents)}
    response = requests.get(url, headers=headers, stream=True, verify=False)

    if 'Content-Disposition' in response.headers.keys():
        decompressed_content = gzip.decompress(response.content)
        soup = BeautifulSoup(decompressed_content, 'xml')
    else:
        soup = BeautifulSoup(response.content, 'xml')
    urls = soup.find_all('loc')

    for url in urls:
        sitemap_url = url.get_text()
        if sitemap_url in crawled_urls:
            print(f"Skipping URL (already crawled): {sitemap_url}")
            continue
        else:
            crawled_urls.add(sitemap_url)

        print(f"Crawling URL: {sitemap_url}")
        status_code, final_url = get_status_code(sitemap_url)
        if status_code is not None:
            print(f"  Status: {status_code}")
            if status_code == 200:
                print(f"  Valid URL")
                writer.writerow([final_url, status_code, valid])
            elif status_code in [301, 302]:
                print(f"  Redirect URL")
                writer.writerow([sitemap_url, status_code, f"Redirect to {final_url}"])
            else:
                print(f"  Invalid URL")
                writer.writerow([sitemap_url, status_code, invalid])
        else:
            print(f"  Need Manual Check")
            writer.writerow([sitemap_url, na, manual])

def main():
    valid = "Valid URL"
    invalid = "Invalid URL"
    na = "N/A"
    manual = "Need Manual Check"

    csv_filename = input("Enter the CSV filename to save/load data: ")
    csv_exists = os.path.exists(csv_filename)

    with open(csv_filename, 'a', newline='') as csv_file:
        fieldnames = ['URL', 'URL Status Code', 'Information']
        writer = csv.writer(csv_file)
        if not csv_exists:
            writer.writerow(fieldnames)

        def signal_handler(signal, frame):
            print("\nScript interrupted. Saving data and exiting...")
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)

        if csv_exists:
            print(f"Resuming from the last crawled URL in '{csv_filename}'...")
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
                        print(f"Skipping URL (already crawled): {full_url}")
                        continue
                    else:
                        crawled_urls.add(full_url)

                    print(f"Crawling URL: {full_url}")
                    status_code, final_url = get_status_code(full_url)
                    if status_code is not None:
                        print(f"  Status: {status_code}")
                        if status_code == 200:
                            print(f"  Valid URL")
                            writer.writerow([final_url, status_code, valid])
                        elif status_code in [301, 302]:
                            print(f"  Redirect URL")
                            writer.writerow([full_url, status_code, f"Redirect to {final_url}"])
                        else:
                            print(f"  Invalid URL")
                            writer.writerow([full_url, status_code, invalid])
                    else:
                        print(f"  Need Manual Check")
                        writer.writerow([full_url, na, manual])

if __name__ == "__main__":
    main()
