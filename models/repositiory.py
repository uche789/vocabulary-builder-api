from typing import List

from sqlalchemy import create_engine, JSON, CheckConstraint, String, Integer
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, sessionmaker
from pydantic import BaseModel

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
    return Vocab(
        word=vocab_instance.word,
        english_translation=vocab_instance.english_translation,
        definition=vocab_instance.definition,
        examples=vocab_instance.examples,
        language=vocab_instance.language,
        word_type=vocab_instance.word_type,
        gender=vocab_instance.gender,
        levels=vocab_instance.levels,
    )

def convert_plain_to_vocab(vocab_instance):
    return Vocab(
        word=vocab_instance['word'],
        english_translation=vocab_instance['english_translation'],
        definition=vocab_instance['definition'],
        examples=vocab_instance['examples'],
        language=vocab_instance['language'],
        word_type=vocab_instance['word_type'],
        gender=vocab_instance['gender'],
        levels=vocab_instance['levels'],
    )

class Repository:
    def __init__(self):
        sqlite_file_name = "database.db"
        sqlite_url = f"sqlite:///{sqlite_file_name}"

        connect_args = {"check_same_thread": False}
        self.engine = create_engine(sqlite_url, connect_args=connect_args)

    def create_db_and_tables(self):
        Base.metadata.create_all(self.engine)

    def get_session(self):
        Session = sessionmaker(bind=self.engine)
        session = Session()
        yield session
        