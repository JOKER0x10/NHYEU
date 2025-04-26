import requests
from bs4 import BeautifulSoup
import os
import re
import sys
from urllib.parse import urljoin
from colorama import Fore, Style, init
import argparse

init(autoreset=True)

class NHYE:
    def __init__(self, url, silent=False):
        self.silent = silent
        self.base_url = re.sub(r'^https?://', '', url.strip())
        self.url = self.base_url.replace('/', '_')
        self.domain_dir = os.path.join(os.getcwd(), "scan_results", self.url)
        os.makedirs(self.domain_dir, exist_ok=True)
        
        try:
            self.response = requests.get(f"https://{self.base_url}", timeout=50)
            self.soup = BeautifulSoup(self.response.text, 'html.parser')
            self.all_links = set()
        except Exception as e:
            if not self.silent:
                print(f"{Fore.RED}Error processing {self.base_url}: {e}{Style.RESET_ALL}")
            self.soup = None

    def get_all_urls(self):
        if not self.soup:
            return

        tags_attrs = [
            ("a", "href"),
            ("link", "href"),
            ("img", "src"),
            ("script", "src"),
            ("iframe", "src"),
            ("form", "action")
        ]

        for tag, attr in tags_attrs:
            for t in self.soup.find_all(tag):
                link = t.get(attr)
                if link:
                    full_link = urljoin(f"https://{self.base_url}", link)
                    self.all_links.add(full_link)

        archive_url = f"https://web.archive.org/cdx/search/cdx?url=*.{self.base_url}/*&output=json&fl=original&collapse=urlkey"
        try:
            res = requests.get(archive_url, timeout=50)
            if res.status_code == 200:
                data = res.json()
                urls = [item[0] for item in data[1:]] if len(data) > 1 else []
                for url in urls:
                    self.all_links.add(url)
        except Exception as e:
            if not self.silent:
                print(f"{Fore.YELLOW}Warning: Could not fetch archive for {self.base_url}: {e}{Style.RESET_ALL}")

    def save_urls(self):
        if not self.all_links:
            return

        file_path = os.path.join(self.domain_dir, "all_urls.txt")
        skip_ext = (".png", ".jpeg", ".jpg", ".gif", ".svg", ".ico", ".css",
                    ".ttf", ".woff", ".woff2", ".eot", ".otf", ".map")
        x = 0

        with open(file_path, "w", encoding="utf-8") as file:
            for link in self.all_links:
                link = link.strip()
                if not link.lower().endswith(skip_ext):
                    x += 1
                    if not self.silent:
                        print(f"🔥:{x} {link}")
                    file.write(f"{link}\n")

        os.system(f"cat {file_path} | httpx -mc 200 > {os.path.join(self.domain_dir, 'all_urls_200.txt')} 2>/dev/null {'&& clear' if not self.silent else ''}")

    def filter_and_save(self, output_filename, condition_func, message):
        if not self.silent:
            print(message)

        input_file = os.path.join(self.domain_dir, "all_urls_200.txt")
        output_file = os.path.join(self.domain_dir, output_filename)
        x = 0

        if not os.path.exists(input_file):
            if not self.silent:
                print(f"{Fore.YELLOW}No valid URLs found for {self.base_url}{Style.RESET_ALL}")
            return

        with open(input_file, "r", encoding="utf-8") as file_in, \
             open(output_file, "w", encoding="utf-8") as file_out:
            for link in file_in:
                link = link.strip()
                if condition_func(link):
                    x += 1
                    if not self.silent:
                        print(f"🔥: {x} {Fore.GREEN}{link}")
                    file_out.write(f"{link}\n")

    def get_all_link_file(self):
        exts = (".xls", ".xml", ".xlsx", ".zip", ".pptx", ".docx", ".sql", ".doc",
                ".pdf", ".json", ".txt", ".csv", ".log", ".conf", ".config", ".cfg",
                ".ini", ".yml", ".yaml", ".tar", ".gz", ".tgz", ".bak", ".7z",
                ".rar", ".cache", ".secret", ".db", ".backup", ".md", ".md5",
                ".exe", ".dll", ".bin", ".bat", ".sh", ".deb", ".rpm", ".iso",
                ".img", ".msi", ".dmg", ".tmp", ".crt", ".pem", ".key", ".pub", ".asc")
        self.filter_and_save(
            "file_url.txt",
            lambda link: link.lower().endswith(exts),
            f"{Fore.RED}--------------------------- files URL ----------------------------------"
        )

    def get_all_link_js(self):
        self.filter_and_save(
            "js_url.txt",
            lambda link: link.lower().endswith(".js"),
            f"{Fore.RED}--------------------------- js URL ----------------------------------"
        )

    def get_all_link_params(self):
        self.filter_and_save(
            "params_url.txt",
            lambda link: "?" in link,
            f"{Fore.RED}--------------------------- params URL ----------------------------------"
        )

def print_scan_results():
    results_dir = os.path.join(os.getcwd(), "scan_results")
    if not os.path.exists(results_dir):
        return

    print(f"\n{Fore.MAGENTA}Scan results:🎉 {Style.RESET_ALL}")
    for domain in os.listdir(results_dir):
        domain_path = os.path.join(results_dir, domain)
        if os.path.isdir(domain_path):
            print(f"{Fore.BLUE}{domain}/{Style.RESET_ALL}")
            for file in sorted(os.listdir(domain_path)):
                print(f"    ├── {Fore.GREEN}{file}{Style.RESET_ALL}")

def process_domain(domain, silent=False):
    if not silent:
        print(f"\n{Fore.CYAN}Processing domain: {domain}{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}The tool is running for 🚀{domain}، Please wait...{Style.RESET_ALL}", end='\r')
    
    nhye = NHYE(domain, silent)
    nhye.get_all_urls()
    if nhye.all_links:
        nhye.save_urls()
        nhye.get_all_link_file()
        nhye.get_all_link_js()
        nhye.get_all_link_params()

def main():
    parser = argparse.ArgumentParser(description='Extract URLs from domains')
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('-f', '--file', help='File containing domains (one per line)')
    group.add_argument('-d', '--domain', help='Single domain to process')
    parser.add_argument('-s', '--silent', action='store_true', help='Run in silent mode (minimal terminal output)')
    parser.add_argument('--show-tree', action='store_true', help='Show directory tree after completion')
    
    args = parser.parse_args()


    os.makedirs("scan_results", exist_ok=True)

    domains = []
    
    if not sys.stdin.isatty():
        domains = [line.strip() for line in sys.stdin if line.strip()]
    elif args.file:
        try:
            with open(args.file, 'r') as f:
                domains = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            if not args.silent:
                print(f"{Fore.RED}Error: File {args.file} not found{Style.RESET_ALL}")
            sys.exit(1)
    elif args.domain:
        domains = [args.domain]
    else:
        parser.print_help()
        sys.exit(1)

    for domain in domains:
        process_domain(domain, args.silent)


    if (not args.silent or args.show_tree):
        print_scan_results()
    elif args.silent:
        print(f"\n{Fore.GREEN} All domains have been successfully processed! ✅{Style.RESET_ALL}")

if __name__ == "__main__":
    x = """
  ██████   █████ █████   █████ █████ █████ ██████████ ██████████  ████████ 
░░██████ ░░███ ░░███   ░░███ ░░███ ░░███ ░░███░░░░░█░███░░░░███ ███░░░░███
 ░███░███ ░███  ░███    ░███  ░░███ ███   ░███  █ ░ ░░░    ███ ░███   ░███
 ░███░░███░███  ░███████████   ░░█████    ░██████         ███  ░░█████████
 ░███ ░░██████  ░███░░░░░███    ░░███     ░███░░█        ███    ░░░░░░░███
 ░███  ░░█████  ░███    ░███     ░███     ░███ ░   █    ███     ███   ░███
 █████  ░░█████ █████   █████    █████    ██████████   ███     ░░████████ 
░░░░░    ░░░░░ ░░░░░   ░░░░░    ░░░░░    ░░░░░░░░░░   ░░░       ░░░░░░░░       

"""

    print(f"{Fore.GREEN}{x}{Style.RESET_ALL}")
    main()