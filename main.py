import json
from typing import Annotated, List
from fastapi import Depends, FastAPI, File, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from models.repositiory import Repository, Vocab, VocabPublic, convert_to_vocab, convert_plain_to_vocab
from contextlib import asynccontextmanager

repo = Repository()

# https://fastapi.tiangolo.com/advanced/events/#lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load DB
    repo.create_db_and_tables()
    yield
    # Clean up (optional)

SessionDep = Annotated[Session, Depends(repo.get_session)]
app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost",
    "http://localhost:5273",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def check_valid_language(lang: str) -> bool: 
    if lang.lower() not in ['de', 'fr', 'jp']:
        raise HTTPException(status_code=400, detail='Invalid language')

@app.get('/vocabulary/')
async def get_vocab(session: SessionDep, lang: str, query = ''):
    check_valid_language(lang)
    if query:
        result = session.query(Vocab).filter(Vocab.language == lang).filter((Vocab.word).contains(query)).order_by(Vocab.word).all()
    else:
        result = session.query(Vocab).filter(Vocab.language == lang).all()
    return result

@app.post('/vocabulary/file')
async def add_vocab(file: UploadFile = File(...)):
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
        print(e)
        raise HTTPException(status_code=400, detail='Invalid file content')
    return

@app.post('/vocabulary/')
async def add_vocab(payload: VocabPublic, session: SessionDep):
    db_vocab =  convert_to_vocab(payload)
    session.add(db_vocab)
    session.commit()
    session.refresh(db_vocab)
    return db_vocab

@app.put('/vocabulary/{vocab_id}')
async def put_vocab(vocab_id, payload: VocabPublic, session: SessionDep):
    db_vocab = session.query(Vocab).filter(Vocab.vocab_id == vocab_id).first()
    if not db_vocab:
        raise HTTPException(status_code=404, detail='Invalid payload')
    db_vocab.definition = payload.definition
    db_vocab.examples = payload.examples
    db_vocab.gender = payload.gender
    db_vocab.word_type = payload.word_type
    db_vocab.word = payload.word
    db_vocab.english_translation = payload.english_translation
    db_vocab.levels = payload.levels
    session.commit()
    session.refresh(db_vocab)
    return db_vocab

@app.delete('/vocabulary/{vocab_id}')
async def delete_vocab(vocab_id, session: SessionDep) -> None:
    db_vocab = session.get(Vocab, vocab_id)
    if not db_vocab:
        return Response(status_code=204)
    session.delete(db_vocab)
    session.commit()
    return

@app.get('/vocabulary/download')
async def generate_vocab(lang: str, session: SessionDep):
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
            'gender': item.gender,
            'levels': item.levels
        })

    with open(fileName, 'w', encoding='utf-8') as f:
        json.dump(list, f)
    return FileResponse(path=fileName, filename=fileName, media_type='application/json')

@app.get('/vocabulary/{vocab_id}')
async def get_vocab_by_id(vocab_id, session: SessionDep):
    db_vocab = session.get(Vocab, vocab_id)
    if not db_vocab:
        raise HTTPException(status_code=404, detail='Not found')
    return db_vocab