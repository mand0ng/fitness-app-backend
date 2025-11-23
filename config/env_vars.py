import os
from dotenv import load_dotenv

def load_config():
    env = os.getenv('ENVIRONMENT', 'development')
    if env == 'production':
        load_dotenv('.env.production', override=False)
    else:
        load_dotenv('.env.development', override=True)