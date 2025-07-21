import os
from datetime import datetime

LOGIN_URL = "https://www.linkedin.com/login"
CONNECTIONS_URL = "https://www.linkedin.com/mynetwork/invite-connect/connections/"

WAIT_TIMEOUT = 10
SCROLL_PAUSE_TIME = 5
MAX_SCROLL_ATTEMPTS = 10

def get_output_filename():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"connections_{timestamp}.json"

FIREFOX_OPTIONS = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-extensions",
    "--disable-gpu"
]