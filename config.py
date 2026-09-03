import os
from dotenv import load_dotenv

load_dotenv()
database_name = os.environ.get('DATABASE_NAME')
database_config = {
    'user': os.environ.get('DATABASE_USER'),
    'password': os.environ.get('DATABASE_PASSWORD'),
    'host': os.environ.get('DATABASE_HOST')
}
api_token = os.environ.get('API_TOKEN')