import bleach
from typing import List

def sanitize(aString) -> str:
    return bleach.clean(aString, tags=[], attributes={}, protocols=[])

def sanitize_all(stringList: List[str] | None):
    if not stringList:
        return None
    for i, item in enumerate(stringList):
        stringList[i] = sanitize(item)

def validate_language(lang: str):
    return lang in ['de', 'fr', 'jp']

def validate_word_type(lang: str):
    return lang in ['Noun', 'Verb', 'Adverb', 'Adjective']

def validate_article(lang: str | None):
    if not lang:
        return True
    return lang in ['f', 'm', 'n', 'p']

def validate_levels(levels: List[str]) -> bool:
    stored_levels = ["Beginner", "Upper Beginner", "Intermediary", "Upper Intermediary", "Advanced", "Fluent"]
    for i, item in enumerate(levels):
        if item not in stored_levels:
            return False
    return True