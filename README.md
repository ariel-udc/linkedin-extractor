# LinkedIn Connections Extractor

A simple CLI tool to extract your LinkedIn connections data.

## Setup

1. Install Firefox browser:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install firefox

# CentOS/RHEL
sudo yum install firefox

# Or download from https://www.mozilla.org/firefox/
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the extractor:
```bash
python linkedin_extractor.py
```

## Usage

```bash
# Basic usage
python linkedin_extractor.py

# Specify output file
python linkedin_extractor.py --output-file my_connections.json

# Run in headless mode
python linkedin_extractor.py --headless
```

## Output

The tool creates a JSON file with:
- Total connection count
- Extraction timestamp
- Array of connections with name, occupation, and profile URL

## Notes

- You'll be prompted for LinkedIn credentials each time
- The tool scrolls through all connections to load them
- LinkedIn's rate limiting may apply
- Ensure you comply with LinkedIn's Terms of Service