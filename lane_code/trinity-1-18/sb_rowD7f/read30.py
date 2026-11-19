"""Print 30 filtered rows in full (five per answer cell) and a source-versus-twin text view for reading."""
import collections as C, hashlib, json, sqlite3
from pathlib import Path

HERE = Path(__file__).resolve().parent; OUT = HERE / 'out'
DB = Path('/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite')
rows = [json.loads(l) for l in open(OUT / 'NEW_ROWS.jsonl')]
maps = [json.loads(l) for l in open(OUT / 'SOURCE_MAP.jsonl')]
con = sqlite3.connect(DB.as_uri() + '?mode=ro&immutable=1', uri=True)
by = C.defaultdict(list)
for r, m in zip(rows, maps):
    by[m['family'], m['label']].append((hashlib.sha256(('READ30|' + r['qid']).encode()).hexdigest(), r, m))
picked = [x for k in sorted(by) for x in sorted(by[k], key=lambda t: t[0])[:5]]
assert len(picked) == 30
full = 'Thirty complete filtered sb_rowD7f rows, five per answer cell (selection: sha256("READ30|"+qid) order).\n\n'
text = 'Source and twin text for the 30 rows of READ30.md (frames are byte-identical to the source; checked by d7/verify_filtered.py).\n\n'
for j, (_, r, m) in enumerate(picked, 1):
    s = json.loads(con.execute('select row from rows where i=?', (m['source_i'],)).fetchone()[0])
    full += f'## {j}. {r["qid"]}\n\n```json\n' + json.dumps(r, ensure_ascii=False, indent=2) + '\n```\n\n'
    text += (f'## {j}. {r["qid"]} {m["family"]} {m["source_label"]} -> {m["label"]}\nSRC Q: {s["student_input"]["question"]}\n'
             f'NEW Q: {r["student_input"]["question"]}\nOPTIONS: {r["student_input"]["options"]} SRC={s["answer"]} NEW={r["answer"]}\n'
             f'SRC T: {s["target"]}\nNEW T: {r["target"]}\n\n')
(OUT / 'READ30.md').write_text(full)
(OUT / 'READ30_TEXT.md').write_text(text)
print(len(picked))
