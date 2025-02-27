import os
from fastapi import HTTPException, Security, status
    
def check_dev_environment():
    env = os.environ.get('FLASK_ENV')
    if env != 'development':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

def check_valid_language(lang: str) -> bool: 
    if lang.lower() not in ['de', 'fr', 'jp']:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid language')
    