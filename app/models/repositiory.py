import os
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy import create_engine, JSON, CheckConstraint, String, Integer
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, sessionmaker
from pydantic import BaseModel
from lib.validation import sanitize_all, sanitize, validate_article, validate_language, validate_levels, validate_word_type

class Base(DeclarativeBase):
    pass

class Vocab(Base):
    __tablename__ = "vocab"

    vocab_id = mapped_column(Integer, primary_key=True, autoincrement=True)
    word = mapped_column(String(250), index=True, nullable=False)
    english_translation: Mapped[str]
    definition: Mapped[List[str] | None] = mapped_column(JSON, nullable=True)
    examples: Mapped[List[str] | None] = mapped_column(JSON, nullable=True)
    language: Mapped[str]
    word_type: Mapped[str]
    article: Mapped[str | None] = mapped_column(String(1), nullable=True)
    levels: Mapped[List[str]] = mapped_column(JSON, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "language IN ('de', 'fr', 'jp')",
            name="language_format_check"
        ),
        CheckConstraint(
            "article IN ('f', 'm', 'n') OR article IS NULL",
            name="article_format_check"
        ),
    )

class VocabPublic(BaseModel):
    word: str
    english_translation: str
    definition: Optional[List[str]] = None
    examples: Optional[List[str]] = None
    language: str
    word_type: str
    article: Optional[str] = None
    levels: List[str]


# Function to convert ExampleTablePublic to ExampleTable
def convert_to_vocab(vocab_instance: VocabPublic):
    if not all([
        validate_word_type(vocab_instance.word_type),
        validate_language(vocab_instance.language),
        validate_levels(vocab_instance.levels),
        validate_article(vocab_instance.article),
    ]):
        raise HTTPException(status_code=400, detail='Invalid arguments')
    
    return Vocab(
        word=sanitize(vocab_instance.word),
        english_translation=sanitize(vocab_instance.english_translation),
        definition=sanitize_all(vocab_instance.definition),
        examples=sanitize_all(vocab_instance.examples),
        language=vocab_instance.language,
        word_type=vocab_instance.word_type,
        article=vocab_instance.article,
        levels=vocab_instance.levels,
    )

def convert_plain_to_vocab(vocab_instance):
    definition = vocab_instance['definition'] if hasattr(vocab_instance, 'definition') else None
    examples = vocab_instance['examples'] if hasattr(vocab_instance, 'examples') else None
    if not all([
        validate_word_type(vocab_instance['word_type']),
        validate_language(vocab_instance['language']),
        validate_levels(vocab_instance['levels']),
        validate_article(vocab_instance['article']),
    ]):
        raise HTTPException(status_code=400, detail='Invalid arguments')

    return Vocab(
        word=sanitize(vocab_instance['word']),
        english_translation=sanitize(vocab_instance['english_translation']),
        definition=sanitize_all(definition),
        examples=sanitize_all(examples),
        language=vocab_instance['language'],
        word_type=vocab_instance['word_type'],
        article=vocab_instance['article'],
        levels=vocab_instance['levels'],
    )

class Repository:
    def __init__(self):
        # sqlite_file_name = "database.db"
        # sqlite_url = f"sqlite:///{sqlite_file_name}"

        # connect_args = {"check_same_thread": False}
        # self.engine = create_engine(sqlite_url, connect_args=connect_args)
        self.engine = create_engine(os.environ.get('DATABASE_URL'))

    def create_db_and_tables(self):
        Base.metadata.create_all(self.engine)

    def get_session(self):
        Session = sessionmaker(bind=self.engine)
        session = Session()
        yield session
        