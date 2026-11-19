"""VSI category pooling for native annotation labels; learned heads receive category text."""
import json
from pathlib import Path
import unicodedata


def normalized(text):
    from trace_format.contracts import new_contracts
    if new_contracts():
        from student_pilot.phrases import normalize_phrase
        return normalize_phrase(str(text))
    return ' '.join(unicodedata.normalize('NFKC', str(text)).casefold().split())


def vocabulary():
    return json.loads(Path(__file__).with_name('vsi_scannet_vocab.json').read_text())
