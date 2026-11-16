"""Invoke the official scorer unchanged; raw model bytes cross this boundary."""
from pathlib import Path
from .paths import evaluator
from .io import load
from offkit.adapt_native import unify
from offkit.report import key

class Scorer:
    def __init__(self, label_file):
        self.label_file = Path(label_file)
        self._labels = None
        self.inputs = []

    def score(self, item, decoded, arm):
        # Ground truth is opened only when a result is scored.
        if self._labels is None:
            data = load(self.label_file)
            self._labels = {key(r):r for r in data}
        raw = decoded['text']
        if not isinstance(raw, str):
            raise TypeError('model text must be a string')
        self.inputs.append(raw.encode('utf-8'))
        task = dict(self._labels[key(item)], thinking=True, benchmark='revsi')
        result = evaluator().score_item(task, raw, len(decoded.get('tokens', [])), cap=2112,
                                        finish=decoded.get('finish', 'stop'))
        row = dict(key=key(item), question_type=item['question_type'], arm=arm, decode=decoded,
                   scores={'answer':result['score']}, call_count=len(decoded.get('calls', [])),
                   call_errors=sum(c.get('kind') == 'error' or c.get('served') is False
                                   for c in decoded.get('calls', [])),
                   no_answer=result['parse_failed'], parse_failed=result['parse_failed'],
                   capped=result['hit_token_cap'])
        record = unify(row)
        if record['refusal']:
            record['score'] = 0.0
        record['parse_failed'] = result['parse_failed']
        record['model_text'] = raw
        record['model_text_hex'] = raw.encode('utf-8').hex()
        return record
