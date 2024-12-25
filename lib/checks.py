import os
import bcrypt
from typing import Annotated
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from fastapi import Depends, HTTPException, Security, status

api_key_header = APIKeyHeader(name="X-API-Key")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def check_api_key(api_key_header: str = Security(api_key_header)):
    stored_api_key = os.getenv('X_API_KEY')
    if stored_api_key != api_key_header:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API Key")
    
def check_dev_environment():
    env = os.environ.get('FLASK_ENV')
    if env != 'development':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

def check_valid_language(lang: str) -> bool: 
    if lang.lower() not in ['de', 'fr', 'jp']:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid language')
    