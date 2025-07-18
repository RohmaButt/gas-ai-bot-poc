import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Vanna.ai Configuration
VANNA_API_KEY = os.getenv('VANNA_API_KEY')
VANNA_MODEL = os.getenv('VANNA_MODEL', 'chinook')  # default model if not specified

# Database Configuration
DATABASE_PATH = os.getenv('DATABASE_PATH', 'retail.db')

# API Configuration
API_HOST = os.getenv('API_HOST', 'localhost')
API_PORT = int(os.getenv('API_PORT', '8000'))
