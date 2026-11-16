"""The sha-pinned phrase table (schema 5.1): instruction -> ordered steps of (target, place), each a phrase and a noun.

The phrase is what the student reads, is asked about and points at; the noun is what SAM 3 detects. Example:
"pick up the black bowl between the plate and the ramekin and place it on the plate" -> target phrase "black bowl
between the plate and the ramekin", noun "black bowl"; place phrase "plate", noun "plate". A step without a place
gives entity 1 a zero row with mask False and no text. Multi-step LIBERO-Long instructions list their steps in order;
the provider uses step 0 unless a subgoal index is given.
"""
import hashlib
import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional

DATA = Path(__file__).parent / 'data'
TABLE_PATH = DATA / 'libero_phrases_v2.json'
TABLE_V1_PATH = DATA / 'libero_phrases.json'
SCHEMA = 'vla-where-phrases-v2'


def normalize(instruction):
    text = re.sub(r'[_\s]+', ' ', str(instruction).strip().lower()).strip()
    text = re.sub(r'^(?:living room|kitchen|study) scene\d+ ', '', text)
    return text.rstrip('.').strip()


@dataclass(frozen=True)
class Phrase:
    phrase: str
    noun: str


@dataclass(frozen=True)
class Step:
    target: Phrase
    place: Optional[Phrase]


class PhraseTable:
    def __init__(self, path=TABLE_PATH):
        raw = Path(path).read_bytes()
        self.path, self.sha256 = Path(path), hashlib.sha256(raw).hexdigest()
        data = json.loads(raw)
        if data.get('schema') != SCHEMA:
            raise ValueError('Unknown phrase table schema')
        self.rows = {}
        for row in data['rows']:
            key = normalize(row['instruction'])
            if key in self.rows:
                raise ValueError('Duplicate instruction in phrase table: ' + key)
            steps = tuple(Step(Phrase(**s['target']), Phrase(**s['place']) if s['place'] else None)
                          for s in row['steps'])
            self.rows[key] = dict(suite=row['suite'], steps=steps)

    def __len__(self):
        return len(self.rows)

    def steps(self, instruction):
        key = normalize(instruction)
        if key not in self.rows:
            raise KeyError('Instruction not in the phrase table: ' + key)
        return self.rows[key]['steps']

    def step(self, instruction, index=0):
        steps = self.steps(instruction)
        return steps[min(index, len(steps) - 1)]

    def suites(self):
        out = {}
        for row in self.rows.values():
            out[row['suite']] = out.get(row['suite'], 0) + 1
        return out


@lru_cache(maxsize=1)
def default_table():
    return PhraseTable()
