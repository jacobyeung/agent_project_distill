"""Invoke the official scorer unchanged; raw model bytes cross this boundary."""
from pathlib import Path
from .paths import evaluator
from .io import load
from offkit.adapt_native import unify, check_not_scripted
from offkit.report import key

class Scorer:
    def __init__(self, label_file, benchmark='revsi999t32'):
        self.label_file = Path(label_file)
        self._labels = None
        self.inputs = []
        self.benchmark = benchmark

    def score(self, item, decoded, arm):
        check_not_scripted(dict(key=key(item), arm=arm, decode=decoded))
        # Ground truth is opened only when a result is scored.
        if self._labels is None:
            import json
            text=self.label_file.read_text()
            data=json.loads(text) if text.lstrip().startswith('[') else [json.loads(s) for s in text.splitlines() if s.strip()]
            self._labels = {key(r):r for r in data}
        raw = decoded['text']
        if not isinstance(raw, str):
            raise TypeError('model text must be a string')
        self.inputs.append(raw.encode('utf-8'))
        task = dict(self._labels[key(item)], thinking=True,
                    benchmark='revsi' if self.benchmark=='revsi999t32' else 'vsibench')
        result = evaluator(self.benchmark).score_item(task, raw, len(decoded.get('tokens', [])), cap=2112,
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
