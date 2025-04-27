# 🌐 NHYE - Advanced Website Link Extractor

**NHYE** is a powerful Python tool for comprehensive link extraction and website reconnaissance. It systematically scans websites to discover all accessible URLs, JavaScript files, parameters, and downloadable resources.

## 🔥 Key Features

- **Complete URL Extraction** (pages, images, scripts, forms)
- **Smart Categorization** of links (files, JS, parameters)
- **Wayback Machine Integration** for historical URL discovery
- **Silent Mode** for background operations
- **Organized Output** with separate directories per domain
- **Multiple Input Methods** (single domain, file input, or stdin)
- **Colorized Output** for better readability
- **HTTPX Integration** to filter live URLs
-------------------------------------------------------------------

![Image](https://github.com/user-attachments/assets/f8d2e2fc-a1a5-42dc-b86a-e7039e2b0c94)


--------------------------------------------------------------------
📂 **Output Structure**
```bash
scan_results/
└── www.example.com/
    ├── all_urls.txt          # All discovered URLs
    ├── all_urls_200.txt      # Only live URLs (status 200)
    ├── file_url.txt          # Downloadable files (PDF, DOCX, etc)
    ├── js_url.txt            # JavaScript files
    └── params_url.txt        # URLs with parameters
└── example.com/
    ├── all_urls.txt          # All discovered URLs
    ├── all_urls_200.txt      # Only live URLs (status 200)
    ├── file_url.txt          # Downloadable files (PDF, DOCX, etc)
    ├── js_url.txt            # JavaScript files
    └── params_url.txt        # URLs with parameters

```
## 🛠 Installation

You must install httpx if you don't have it `go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest`
```bash
git clone https://github.com/NHYE79/NHYEU.git
cd NHYEU
python3 -m venv NHYEU
source NHYEU/bin/activate
pip3 install -r requirements.txt
sudo chmod +x NHYE.py
```
## using

Basic usage

```bash
python3 NHYE.py -d example.com
```
## You can also scan more than one target
```bash
1 python3 NHYE.py -f domain.txt
2 cat domain.txt | python3 NHYE.py
```
## `-s` Silent mode (minimal output)
```bash
python3 NHYE.py -d example.com -s
```
## 📌Advanced Uses
```bash
cat scan_results/example.com/js_url.txt | nuclei -t nuclei-templates/http/exposures/

cat scan_results/example.com/params_url.txt | sqlmap --level 3  --risk 3 --random-agent --tamper=space2hash,space2comment
```
## Use in scripts:
```bash
from NHYE import NHYE
scanner = NHYE("example.com")
scanner.get_all_urls()
```
