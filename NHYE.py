import asyncio
import httpx
import os
import re
import json
from typing import Set, Dict, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from colorama import Fore, Style, init
from tqdm.asyncio import tqdm_asyncio
import argparse

# Initialize colorama
init(autoreset=True)

class NHYEX_Optimized:

    TIMEOUT_SECONDS = 30
    MAX_CONNECTIONS = 50
    RESULTS_FOLDER = "scan_results"
    

    IGNORED_PATHS = {
        'admin', 'wp-admin', 'webmail', '.git', 'backup',
        'test', 'tmp', 'temp', 'old', 'dev', 'development',
        'robots.txt', 'sitemap.xml'
    }
    

    IGNORED_EXTENSIONS = {
        '.jpg', '.jpeg', '.png', '.gif', '.ico', '.svg',
        '.css', '.map', '.woff', '.ttf', '.eot'
    }
    
    def __init__(self, domain: str, dynamic: bool = False, silent: bool = False):

        if not domain or not domain.strip():
            raise ValueError("Domain cannot be empty")
            
        self.domain = domain.strip().replace('https://', '').replace('http://', '').rstrip('/')
        self.dynamic = dynamic
        self.silent = silent
        
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(self.TIMEOUT_SECONDS, connect=10),
            limits=httpx.Limits(max_connections=self.MAX_CONNECTIONS),
            follow_redirects=True,
            verify=False  # تجاهل أخطاء شهادات SSL
        )
        
        self.active_data = {
            'urls': set(),
            'js': set(),
            'files': set(),
            'params': set(),
            'emails': set(),
            'phones': set()
        }
        
        self._processed_urls = set()
        self._error_types = set()
        
        self.result_dir = os.path.join(self.RESULTS_FOLDER, self.domain)
        os.makedirs(self.result_dir, exist_ok=True)
        
    async def fetch_from_wayback(self):
        """جلب الروابط الأرشيفية من Wayback Machine"""
        wayback_url = f"https://web.archive.org/cdx/search/cdx?url={self.domain}/*&output=json&fl=original&collapse=digest"
        try:
            res = await self.session.get(wayback_url)
            if res.status_code == 200:
                data = res.json()
                wayback_urls = [entry[0] for entry in data[1:]] 
                
                tasks = [self.process_url(url) for url in wayback_urls]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                if not self.silent:
                    for result in results:
                        if isinstance(result, Exception):
                            print(f"{Fore.RED}Task Error: {result}{Style.RESET_ALL}")
                
        except Exception as e:
            if not self.silent:
                print(f"{Fore.RED}Wayback Machine Error: {e}{Style.RESET_ALL}")

    def _should_process_url(self, url: str) -> bool:

        try:
    
            path = url.split('/')[-1].lower()
            if any(ignored in url.lower() for ignored in self.IGNORED_PATHS):
                return False
                
   
            if any(path.endswith(ext) for ext in self.IGNORED_EXTENSIONS):
                return False
                
            return True
        except:
            return True
    
    def _normalize_url(self, url: str) -> str:

        url = url.lower()
        url = url.replace('http://', '').replace('https://', '')
        url = url.replace('www.', '')
        if ':80/' in url:
            url = url.replace(':80/', '/')
        return url

    async def process_url(self, url: str) -> bool:
     
        normalized_url = self._normalize_url(url)
        if normalized_url in self._processed_urls:
            return False
            

        if not self._should_process_url(url):
            return False
        
        self._processed_urls.add(normalized_url)
        
        try:
            for _ in range(2):  
                try:
                    response = await self.session.get(url)
                    if response.status_code == 200:
                        self._categorize_url(url, response)
                        return True
                    break  
                except httpx.TimeoutException:
                    continue 
                except Exception as e:
                    break
        except Exception as e:
            if not self.silent:
                error_key = f"{normalized_url}"
                if error_key not in self._error_types:
                    self._error_types.add(error_key)
                    print(f"{Fore.RED}Processing error {url}{Style.RESET_ALL}")
        return False

    def _categorize_url(self, url, response=None):
  
        self.active_data['urls'].add(url)
        
        # تصنيف حسب نوع الرابط
        if url.endswith('.js'):
            self.active_data['js'].add(url)
            if response:
                self._extract_from_js(response.text)
        elif '?' in url:
            self.active_data['params'].add(url)
        
        # تصنيف الملفات
        file_exts = (".xls", ".xml", ".xlsx", ".zip", ".pptx", ".docx", ".sql",".doc", ".PDF", ".pdf", ".json", ".txt", ".csv", ".log", ".conf", ".config", ".cfg", ".ini", ".yml", ".yaml", ".tar", ".gz", ".tgz", ".bak", ".7z", ".rar", ".cache", ".secret", ".db", ".backup", ".md", ".md5", ".exe", ".dll", ".bin", ".bat", ".sh", ".tar", ".deb", ".rpm", ".iso", ".img", ".msi", ".dmg", ".tmp", ".crt", ".pem", ".key", ".pub", ".asc")
        if any(url.endswith(ext) for ext in file_exts):
            self.active_data['files'].add(url)

    def _extract_from_js(self, js_text):
   
        self.active_data['emails'].update(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', js_text))
        self.active_data['phones'].update(re.findall(r'\b(?:\+?\d{1,3}[\s-]?)?\d{7,15}\b(?=\s|$)', js_text))

    async def crawl(self):

        base_url = f"https://{self.domain}"
        res = await self.session.get(base_url)
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            tasks = set()
            
            for tag, attr in [("a", "href"), ("link", "href"), ("img", "src"), ("script", "src")]:
                for element in soup.find_all(tag):
                    if link := element.get(attr):
                        full_url = urljoin(base_url, link)
                        try:
                            # Validate the URL
                            httpx.URL(full_url)
                            tasks.add(self.process_url(full_url))
                        except httpx.InvalidURL:
                            if not self.silent:
                                print(f"{Fore.RED}Invalid URL skipped: {full_url}{Style.RESET_ALL}")
            
            await tqdm_asyncio.gather(*tasks, desc="Crawling URLs", disable=self.silent)

    async def save_results(self):

        for name, data in self.active_data.items():
            if data:
                file_path = os.path.join(self.result_dir, f"{name}.txt")
                with open(file_path, "w", encoding="utf-8") as f:
                    for item in sorted(data):
                        f.write(item + "\n")

    async def __aenter__(self) -> 'NHYEX_Optimized':

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:

        await self.session.aclose()

    async def run(self) -> None:

        try:
            if not self.silent:
                print(f"{Fore.CYAN}🚀 Starting scan for {self.domain}...{Style.RESET_ALL}")
            

            await asyncio.gather(
                self.crawl(),
                self.fetch_from_wayback()
            )
            
            await self.save_results()
            

            total_items = sum(len(data) for data in self.active_data.values())
            
            if not self.silent:
                print(f"\n{Fore.GREEN}✅ Scan completed! Results:{Style.RESET_ALL}")
                for name, data in self.active_data.items():
                    print(f"{Fore.YELLOW}• {name.capitalize()}: {len(data)}{Style.RESET_ALL}")
                print(f"\n📁 Saved to: {self.result_dir}")

        except Exception as e:
            if not self.silent:
                print(f"\n{Fore.RED}❌ Error: {str(e)}{Style.RESET_ALL}")
        finally:
            await self.session.aclose()

def clean_domain(domain: str) -> str:

    domain = domain.strip().lower()
    domain = domain.replace('https://', '').replace('http://', '')
    domain = domain.replace('www.', '')
    if domain.endswith('/'):
        domain = domain[:-1]
    return domain

async def scan_multiple_domains(domains, dynamic=False, silent=False):

    for domain in domains:
        try:
            clean_domain_name = clean_domain(domain)
            print(f"\n{Fore.CYAN}Domain scanning in progress: {domain}{Style.RESET_ALL}")
            scanner = NHYEX_Optimized(clean_domain_name, dynamic, silent)
            await scanner.run()
            print(f"{Fore.GREEN}Domain scan completed: {domain}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Domain scan error {domain}: {str(e)}{Style.RESET_ALL}")

def main():
    parser = argparse.ArgumentParser(description="Web Scanner Tool")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-d", "--domain", help="One domain for scanning")
    group.add_argument("-l", "--list", help="A file path containing a list of domains")
    parser.add_argument("--dynamic", help="Dynamic Scan Activation", action="store_true")
    parser.add_argument("--silent", help="Hide error messages", action="store_true")
    
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    args = parser.parse_args()
    
    domains = []
    if args.domain:
        domains = [args.domain]
    elif args.list:
        try:
            with open(args.list, 'r') as f:
                domains = [line.strip() for line in f if line.strip()]
            print(f"{Fore.CYAN}Downloaded {len(domains)} Domain from the file{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error reading the domains file: {str(e)}{Style.RESET_ALL}")
            return
    
    if not domains:
        print(f"{Fore.RED}No domains have been selected for testing{Style.RESET_ALL}")
        return
        
    asyncio.run(scan_multiple_domains(domains, args.dynamic, args.silent))

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
    try:
        main()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
