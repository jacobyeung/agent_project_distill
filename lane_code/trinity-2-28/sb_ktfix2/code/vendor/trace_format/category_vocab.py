"""VSI category pooling for native annotation labels; learned heads receive category text."""
import json
from pathlib import Path
import unicodedata


def normalized(text):
    return ' '.join(unicodedata.normalize('NFKC', str(text)).casefold().split())


def vocabulary():
    return json.loads(Path(__file__).with_name('vsi_scannet_vocab.json').read_text())
