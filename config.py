import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    NEWSAPI_KEY = os.getenv('NEWSAPI_KEY')

    @classmethod
    def validate(cls):
        """Validate required configuration variables."""
        required_vars = ['OPENAI_API_KEY', 'NEWSAPI_KEY']
        missing_vars = [var for var in required_vars if not getattr(cls, var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")