"""Relative count on dev-S1 (family main, task relative_count): accuracy and count of numeric (non-letter) predictions. usage: relcount.py ITEMS.jsonl [...]"""
import json, re, sys
for p in sys.argv[1:]:
    rows = [r for r in map(json.loads, open(p)) if r.get('family') == 'main' and r.get('task_type') == 'relative_count']
    num = sum(1 for r in rows if not re.fullmatch(r'\s*[A-Za-z]\s*', str(r.get('prediction') or '')))
    print('%s n %d acc %.2f numeric_or_nonletter_predictions %d' % (p, len(rows), 100 * sum(float(r['score']) for r in rows) / max(1, len(rows)), num))
