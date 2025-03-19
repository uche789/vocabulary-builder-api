import os
from typing import List

from fastapi import HTTPException
from sqlalchemy import create_engine, JSON, CheckConstraint, String, Integer
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, sessionmaker
from pydantic import BaseModel
from lib.validation import sanitize_all, sanitize, validate_gender, validate_language, validate_levels, validate_word_type

class Base(DeclarativeBase):
    pass

class Vocab(Base):
    __tablename__ = "vocab"

    vocab_id = mapped_column(Integer, primary_key=True, autoincrement=True)
    word = mapped_column(String(250), index=True, unique=True)
    english_translation: Mapped[str]
    definition: Mapped[List[str] | None] = mapped_column(JSON, nullable=True)
    examples: Mapped[List[str] | None] = mapped_column(JSON, nullable=True)
    language: Mapped[str]
    word_type: Mapped[str]
    gender: Mapped[str | None] = mapped_column(String(1), nullable=True)
    levels: Mapped[List[str] | None] = mapped_column(JSON, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "language IN ('de', 'fr', 'jp')",
            name="language_format_check"
        ),
        CheckConstraint(
            "gender IN ('f', 'm', 'n') OR gender IS NULL",
            name="gender_format_check"
        ),
    )

class VocabPublic(BaseModel):
    word: str
    english_translation: str
    definition: List[str] | None
    examples: List[str] | None
    language: str
    word_type: str
    gender: str | None
    levels: List[str] | None


# Function to convert ExampleTablePublic to ExampleTable
def convert_to_vocab(vocab_instance: VocabPublic):
    if not all([
        validate_word_type(vocab_instance.word_type),
        validate_language(vocab_instance.language),
        validate_levels(vocab_instance.levels),
        validate_gender(vocab_instance.gender),
    ]):
        raise HTTPException(status_code=400, detail='Invalid arguments')
    
    return Vocab(
        word=sanitize(vocab_instance.word),
        english_translation=sanitize(vocab_instance.english_translation),
        definition=sanitize_all(vocab_instance.definition),
        examples=sanitize_all(vocab_instance.examples),
        language=vocab_instance.language,
        word_type=vocab_instance.word_type,
        gender=vocab_instance.gender,
        levels=vocab_instance.levels,
    )

def convert_plain_to_vocab(vocab_instance):
    if not all([
        validate_word_type(vocab_instance['word_type']),
        validate_language(vocab_instance['language']),
        validate_levels(vocab_instance['levels']),
        validate_gender(vocab_instance['gender']),
    ]):
        raise HTTPException(status_code=400, detail='Invalid arguments')
    
    return Vocab(
        word=sanitize(vocab_instance['word']),
        english_translation=sanitize(vocab_instance['english_translation']),
        definition=sanitize_all(vocab_instance['definition']),
        examples=sanitize_all(vocab_instance['examples']),
        language=vocab_instance['language'],
        word_type=vocab_instance['word_type'],
        gender=vocab_instance['gender'],
        levels=vocab_instance['levels'],
    )

class Repository:
    def __init__(self):
        # sqlite_file_name = "database.db"
        # sqlite_url = f"sqlite:///{sqlite_file_name}"

        # connect_args = {"check_same_thread": False}
        # self.engine = create_engine(sqlite_url, connect_args=connect_args)
        print(os.environ.get('DATABASE_USER'), os.environ.get('DATABASE_URL'))
        self.engine = create_engine(os.environ.get('DATABASE_URL'))

    def create_db_and_tables(self):
        Base.metadata.create_all(self.engine)

    def get_session(self):
        Session = sessionmaker(bind=self.engine)
        session = Session()
        yield session
        