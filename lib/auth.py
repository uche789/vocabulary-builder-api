from datetime import datetime, timedelta, timezone
import os
import bcrypt
from fastapi import HTTPException, Request
import jwt

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

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
    expire = datetime.now(timezone.utc) + timedelta(minutes=5)
    # expire = datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=48)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def check_token(request: Request):
    print(request.cookies)

def verify_access(token: str):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception