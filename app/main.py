import json
import logging
import os
from dotenv import load_dotenv
from typing import Annotated, List
from fastapi import Depends, FastAPI, File, HTTPException, Response, UploadFile, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from models.repositiory import Repository, Vocab, VocabPublic, convert_to_vocab, convert_plain_to_vocab
from contextlib import asynccontextmanager
from lib.checks import check_dev_environment, check_valid_language
from lib.auth import generate_access_token, authenticate_user, verify_access, validate_api_key
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from slowapi.errors import RateLimitExceeded
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("app.log") # Log to file
        ]
    )
logger = logging.getLogger('tomostudy.logger')

load_dotenv()
repo = Repository()

# https://fastapi.tiangolo.com/advanced/events/#lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load DB
    repo.create_db_and_tables()
    yield
    # Clean up (optional)

SessionDep = Annotated[Session, Depends(repo.get_session)]
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

origins = []
if os.environ.get('FLASK_ENV') == 'development':
    origins = [
        "http://localhost",
        "http://localhost:5273",
    ]
else:
    origins = [
        os.environ.get('ALLOW_ORIGIN')
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post('/login')
@limiter.limit("50/minute")
async def login(request: Request, response: Response, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    authenticate_user(password=form_data.password, username=form_data.username)
    token = generate_access_token(form_data.username)
    # response.set_cookie('access_token', token, httponly=True, secure=True, samesite='Strict', path='/')
    response.set_cookie('access_token', token, httponly=True, samesite='Strict', path='/')
    return

@app.get('/auth', dependencies=[Depends(verify_access)])
@limiter.limit("200/minute")
async def auth(request: Request):
    return

@app.post('/logout')
@limiter.limit("50/minute")
def logout(request: Request, response: Response):
    response.set_cookie("access_token", "", max_age=0)  # Delete access token
    return

@app.get('/vocabulary/', dependencies=[Depends(validate_api_key)])
@limiter.limit("200/minute")
async def get_vocab(request: Request, session: SessionDep, lang: str, query = ''):
    check_valid_language(lang)
    if query:
        if len(query) > 100 or not isinstance(query, str):  # Limit length
            return []
        result = session.query(Vocab).filter(Vocab.language == lang).filter((Vocab.word.ilike(f"%{query}%"))).order_by(Vocab.word).all()
    else:
        result = session.query(Vocab).filter(Vocab.language == lang).all()
    return result

@app.get('/vocabulary/{vocab_id}', dependencies=[Depends(validate_api_key)])
@limiter.limit("200/minute")
async def get_vocab_by_id(request: Request, vocab_id: int, session: SessionDep):
    db_vocab = session.get(Vocab, vocab_id)
    if not db_vocab:
        raise HTTPException(status_code=404, detail='Not found')
    return db_vocab

@app.get('/vocabulary/slug/{slug}', dependencies=[Depends(validate_api_key)])
@limiter.limit("200/minute")
async def get_vocab_by_slug(request: Request, slug: str, lang: str, session: SessionDep):
    result = session.query(Vocab).filter(Vocab.language == lang).filter(Vocab.word == slug) .order_by(Vocab.word).first()
    if not result:
        raise HTTPException(status_code=404, detail='Not found')
    return result


@app.post('/vocabulary/file', dependencies=[Depends(verify_access)])
@limiter.limit("200/minute")
async def add_vocab(request: Request, file: UploadFile = File(...)):
    if file.content_type != 'application/json':
        raise HTTPException(status_code=400, detail='Invalid file type ' + file.content_type + '. Please add a JSON file')
    dataString = await file.read()
    data = json.loads(dataString)
    if not isinstance(data, List):
        raise HTTPException(status_code=400, detail='Invalid file content')
    
    session = Session(repo.engine)

    try:
        for item in data:
            db_vocab = convert_plain_to_vocab(item)
            session.add(db_vocab)
        session.commit()
        session.close()
    except Exception as e:
        logger.error(f"Failed to upload file content: {e}")
        raise HTTPException(status_code=400, detail='Failed to upload file content')
    return

@app.post('/vocabulary/', dependencies=[Depends(verify_access)])
@limiter.limit("200/minute")
async def add_vocab(request: Request, payload: VocabPublic, session: SessionDep):
    db_vocab =  convert_to_vocab(payload)
    session.add(db_vocab)
    session.commit()
    session.refresh(db_vocab)
    return db_vocab

@app.put('/vocabulary/{vocab_id}', dependencies=[Depends(verify_access)])
@limiter.limit("200/minute")
async def put_vocab(request: Request, vocab_id, payload: VocabPublic, session: SessionDep):
    db_vocab = session.query(Vocab).filter(Vocab.vocab_id == vocab_id).first()
    if not db_vocab:
        raise HTTPException(status_code=404, detail='Invalid payload')
    db_vocab.definition = payload.definition
    db_vocab.examples = payload.examples
    db_vocab.article = payload.article
    db_vocab.word_type = payload.word_type
    db_vocab.word = payload.word
    db_vocab.english_translation = payload.english_translation
    db_vocab.levels = payload.levels
    session.commit()
    session.refresh(db_vocab)
    return db_vocab

@app.delete('/vocabulary/{vocab_id}', dependencies=[Depends(verify_access)])
@limiter.limit("100/minute")
async def delete_vocab(request: Request, vocab_id, session: SessionDep) -> None:
    db_vocab = session.get(Vocab, vocab_id)
    if not db_vocab:
        return Response(status_code=204)
    session.delete(db_vocab)
    session.commit()
    return Response(status_code=200)

@app.get('/vocabulary/download', dependencies=[Depends(verify_access)])
@limiter.limit("50/minute")
async def generate_vocab(request: Request, lang: str, session: SessionDep):
    check_dev_environment()
    check_valid_language(lang)
    fileName = 'output/' + lang + '.json'
    rawList = session.query(Vocab).where(Vocab.language == lang).all()

    list = []
    for item in rawList:
        list.append({
            'vocab_id': item.vocab_id,
            'word': item.word,
            'english_translation': item.english_translation,
            'word_type': item.word_type,
            'definition': item.definition,
            'examples': item.examples,
            'article': item.article,
            'levels': item.levels
        })

    with open(fileName, 'w', encoding='utf-8') as f:
        json.dump(list, f)
    return FileResponse(path=fileName, filename=fileName, media_type='application/json')