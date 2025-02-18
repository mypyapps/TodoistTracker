import os
from dotenv import load_dotenv

load_dotenv()

# Configuration settings
TODOIST_API_TOKEN = os.environ.get('TODOIST_API_TOKEN') 
CACHE_TIMEOUT = 300  # 5 minutes cache 
