import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
SONAR_API_KEY = os.getenv('SONAR_API_KEY')
SONAR_BASE_URL = "https://api.perplexity.ai/chat/completions"
SS_USERNAME = os.getenv('SS_USERNAME')
SS_API_KEY = os.getenv('SS_API_KEY')

# Business Logic Constants
PRINTING_COST = 1.50
PROFIT_MARGIN = 10.00

# Conversation Settings
MAX_HISTORY = 10
TIMEOUT_MINUTES = 30

# Server Settings
PORT = 5001
DEBUG = True