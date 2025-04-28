# NHYE Web Scanner

A high-performance, asynchronous web reconnaissance tool designed for efficient website analysis and information gathering.

## 🚀 Features

- **Fast Concurrent Scanning**: Utilizes Python's asyncio for efficient parallel processing
- **Historical Data**: Integrates with Wayback Machine for comprehensive URL discovery
- **Multiple Data Collection**:
  - URLs and endpoints
  - JavaScript files
  - Parameter discovery
  - Email addresses
  - Phone numbers
  - File enumeration
----------------------------------------------------------------------------------
![Image](https://github.com/user-attachments/assets/3cab55e0-60a0-4a32-ba87-d05d95e515ea)
----------------------------------------------------------------------------------
## 🛠️ Installation

```bash
# Clone the repository
git clone https://github.com/NHYE79/NHYEU.git
cd NHYEU
python3 -m venv NHYEU
source NHYEU/bin/activate
# Install requirements
pip3 install -r requirements.txt
```

## 💻 Usage

```bash
# Scan a single domain
python NHYEU.py -d example.com

# Scan multiple domains from a file
python NHYEU.py -l domains.txt

# Enable dynamic scanning
python myapp.py -d example.com --dynamic

# Silent mode (suppress error messages)
python myapp.py -d example.com --silent
```

## 🔍 Key Features

- Asynchronous HTTP requests for faster scanning
- Smart URL normalization to avoid duplicates
- Built-in error handling and retry mechanisms
- Organized results storage in JSON format
- Progress tracking with colorized output
- Configurable connection settings

## 📝 Output

Results are automatically saved in the `scan_results` directory, organized by domain name. Each scan creates separate `TXT` files for:
- Discovered URLs
- JavaScript files
- Parameters
- Emails
- Phone numbers
- General files

## ⚠️ Disclaimer

This tool is for educational and authorized security testing purposes only. Always obtain proper permission before scanning any website.

## 📄 License

MIT License - feel free to use and modify as needed.
