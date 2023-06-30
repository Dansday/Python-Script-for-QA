import requests
import gzip
from bs4 import BeautifulSoup
import time
import random
import csv
import os
import signal
import sys

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
        response = requests.get(url, headers=headers, timeout=30)
        time.sleep(0.1)
        return response.status_code
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

    return None

def crawl_sitemap(url, writer):
    valid = "Valid Backref URL"
    invalid = "Invalid Backref URL"
    no_href = "No Href Found"
    no_hreflang = "No Hreflang Found"
    no_both = "No Hreflang and Href Found"
    invalid_status = "Invalid Backref URL Status Code"
    na = "N/A"
    manual = "Need Manual Check"
    headers = {'User-Agent': random.choice(user_agents)}
    response = requests.get(url, headers=headers, stream=True)
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
        status_code = get_status_code(sitemap_url)
        if status_code is not None:
            print(f"  Status: {status_code}")
            response = requests.get(sitemap_url, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            link_tags = soup.find_all('link', rel='alternate')
            if link_tags:
                for link_tag in link_tags:
                    hreflang = link_tag.get('hreflang')
                    href = link_tag.get('href')
                    print(f"  hreflang: {hreflang}, href: {href}")
                    backref_status = get_status_code(href)
                    if backref_status is not None:
                        print(f"  Backref Status: {backref_status}")
                        if backref_status == 200:
                            backref_soup = BeautifulSoup(requests.get(href, headers=headers).content, 'html.parser')
                            backref_link_tags = backref_soup.find_all('link', rel='alternate')
                            if any(tag.get('href') == sitemap_url for tag in backref_link_tags):
                                print(f"    {valid}")
                                writer.writerow([sitemap_url, status_code, hreflang, href, backref_status, valid])
                            else:
                                print(f"    {invalid}")
                                writer.writerow([sitemap_url, status_code, hreflang, href, backref_status, invalid])
                        else:
                            print(f"    {invalid_status}: {backref_status}")
                            writer.writerow([sitemap_url, status_code, hreflang, href, backref_status, invalid_status])
                    else:
                        print(f"    {manual}")
                        writer.writerow([sitemap_url, status_code, hreflang, href, na, manual])
            else:
                print(f"  {no_hreflang}")
                writer.writerow([sitemap_url, status_code, no_href, no_hreflang, na, no_both])
        else:
            print(f"  {manual}")
            writer.writerow([sitemap_url, na, na, na, na, manual])

def crawl_sitemap_index(url, csv_file):
    headers = {'User-Agent': random.choice(user_agents)}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'xml')
    sitemaps = soup.find_all('loc')

    for sitemap in sitemaps:
        sitemap_url = sitemap.get_text()
        print(f"Crawling sitemap: {sitemap_url}")
        if sitemap_url.endswith(".xml"):
            crawl_sitemap(sitemap_url, csv_file)
        else:
            crawl_nested_sitemap(sitemap_url, csv_file)

def crawl_nested_sitemap(url, csv_file):
    headers = {'User-Agent': random.choice(user_agents)}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    tbody = soup.find('tbody')
    if tbody:
        rows = tbody.find_all('tr')
        for row in rows:
            loc = row.find('td', class_='loc')
            if loc:
                child_sitemap_url = loc.find('a').get('href')
                print(f"Crawling child sitemap: {child_sitemap_url}")
                crawl_sitemap(child_sitemap_url, csv_file)

def main():
    csv_filename = input("Enter the CSV filename to save/load data: ")
    csv_exists = os.path.exists(csv_filename)

    with open(csv_filename, 'a', newline='') as csv_file:
        fieldnames = ['URL', 'URL Status Code', 'Hreflang', 'Href', 'Backref URL Status Code', 'Backref Information']
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

        sitemap_index_url = input("Enter the sitemap index: ")
        crawl_sitemap_index(sitemap_index_url, writer)

if __name__ == "__main__":
    main()
