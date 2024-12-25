from datetime import datetime, timedelta, timezone
import os
import bcrypt
from fastapi import HTTPException, Request, status
import jwt

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = "HS256"

# def get_hash_password(password: str):
#     pwd_bytes = password.encode('utf-8')
#     salt = bcrypt.gensalt()
#     hashed_password = bcrypt.hashpw(password=pwd_bytes, salt=salt)
#     return hashed_password

def verify_password(password: str):
    try:
        hashed_password = os.getenv('USER_PASSWORD')
        check = bcrypt.checkpw(password=password.encode('utf-8'), hashed_password=hashed_password.encode('utf-8'))
        return check
    except Exception as e:
        return False
    
def authenticate_user(username: str, password: str):
    if username != os.getenv('USER_NAME'):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    if not verify_password(password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    return username

def generate_access_token(username: str):
    to_encode = {'sub': username}
    expiry_minutes = 720
    if os.getenv('FLASK_ENV') == 'development':
        expiry_minutes = 15
    expire = datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_access(request: Request):
    token = request.cookies.get('access_token')
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    check_token(token=token)
    

def check_token(token: str):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials"
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception