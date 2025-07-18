# LinkedIn Extractors

Two CLI tools to extract LinkedIn connection data.

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

3. (Optional) Set up credentials in .env file:
```bash
cp .env.example .env
# Edit .env with your LinkedIn credentials
```

## Tools

### 1. Your Own Connections Extractor (`linkedin_extractor.py`)

Extracts all connections from your own LinkedIn profile.

```bash
# Basic usage
python linkedin_extractor.py

# Specify output file
python linkedin_extractor.py --output-file my_connections.json

# Run in headless mode
python linkedin_extractor.py --headless

# Keep browser open for debugging
python linkedin_extractor.py --keep-browser-open
```

### 2. Profile Contacts Extractor (`profile_contacts_extractor.py`)

Extracts contacts from a specific LinkedIn profile by visiting their profile and clicking the "contacts" link.

```bash
# Basic usage
python profile_contacts_extractor.py "https://www.linkedin.com/in/someprofile/"

# Specify output file
python profile_contacts_extractor.py "https://www.linkedin.com/in/someprofile/" --output-file profile_contacts.json

# Run in headless mode
python profile_contacts_extractor.py "https://www.linkedin.com/in/someprofile/" --headless

# Keep browser open for debugging
python profile_contacts_extractor.py "https://www.linkedin.com/in/someprofile/" --keep-browser-open
```

## Credentials

Both tools support reading credentials from a `.env` file:

1. Copy the example: `cp .env.example .env`
2. Edit `.env` with your credentials:
```
LINKEDIN_EMAIL=your-email@example.com
LINKEDIN_PASSWORD=your-password-here
```

If no `.env` file is found, you'll be prompted to enter credentials manually.

## Output

Both tools create JSON files with:

### linkedin_extractor.py output:
```json
{
  "total_connections": 150,
  "extracted_at": "2025-07-18 15:30:00",
  "connections": [
    {
      "name": "John Doe",
      "occupation": "Software Engineer",
      "profile_url": "https://www.linkedin.com/in/johndoe"
    }
  ]
}
```

### profile_contacts_extractor.py output:
```json
{
  "profile_url": "https://www.linkedin.com/in/someprofile/",
  "total_contacts": 75,
  "extracted_at": "2025-07-18 15:30:00",
  "contacts": [
    {
      "name": "Jane Smith",
      "alternative_name": "Jane M. Smith",
      "job_position": "Product Manager",
      "location": "New York, NY",
      "profile_url": "https://www.linkedin.com/in/janesmith"
    }
  ]
}
```

## Features

- **Automatic pagination**: Loads all pages of results
- **2FA support**: Handles LinkedIn verification codes
- **Duplicate prevention**: Avoids extracting the same contact twice
- **Detailed logging**: Shows progress and extracted data
- **Browser debugging**: Keep browser open to inspect pages
- **Headless mode**: Run without GUI for automation

## Notes

- LinkedIn credentials are required for both tools
- The tools respect LinkedIn's page loading and navigation
- LinkedIn's rate limiting and terms of service apply
- Always ensure compliance with LinkedIn's Terms of Service
- Use `--keep-browser-open` for debugging and verification