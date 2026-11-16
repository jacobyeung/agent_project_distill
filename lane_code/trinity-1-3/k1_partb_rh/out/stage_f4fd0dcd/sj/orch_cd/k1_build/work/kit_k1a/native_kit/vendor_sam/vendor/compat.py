from types import SimpleNamespace
from kitlib import load_cache as cache,decode
from phrase import normalize_phrase
def tower():return SimpleNamespace(phrase=normalize_phrase,rle_decode=decode)
