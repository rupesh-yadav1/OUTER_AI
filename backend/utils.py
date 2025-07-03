# backend/utils.py

import re
import difflib
import unicodedata
from typing import List

def clean_unicode(txt: str) -> str:
    """
    Normalize Unicode (NFKC) and replace common non-ASCII dashes with '-'.
    """
    s = unicodedata.normalize("NFKC", txt)
    # replace various dash characters with ASCII hyphen
    for dash in ["\u2010","\u2011","\u2012","\u2013","\u2014","\u2015"]:
        s = s.replace(dash, "-")
    return s

def fuzzy_contains(text: str, keywords: List[str], cutoff: float = 0.75) -> bool:
    """
    Return True if any word in `text` matches a keyword with similarity ≥ cutoff.
    This lets us catch typos like "mathh" or "analyz".
    """
    words = re.findall(r"\w+", text.lower())
    for w in words:
        for k in keywords:
            if difflib.SequenceMatcher(None, w, k).ratio() >= cutoff:
                return True
    return False
