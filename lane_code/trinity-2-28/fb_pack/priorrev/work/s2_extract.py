"""Extract per-row facts from the reconstructed VQA population and verify each row
against its source bytes (v7 store row or twin line). Output: work/rows.pkl."""
import hashlib, importlib.util, json, pickle, re, sqlite3, sys
from multiprocessing import Pool
from pathlib import Path

W = Path(__file__).resolve().parent
FB = Path('/scratch/jjyeung/orch_n30/fb_pack')
ELIG = FB/'prior2b/work/source/eligible_vqa.sqlite'
V7 = FB/'ro/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite'
TWINS = FB/'ro/orch_n30/sb_rowD7f/out/NEW_ROWS.jsonl'
sys.path.insert(0, str(W/'new'))
from student_pilot.r1_direction_twins import direction_details  # patched parser
from student_pilot.r1_population import family, TYPES
from student_pilot.p3_provenance import digest

spec = importlib.util.spec_from_file_location('student_pilot._base_twins', W/'base/student_pilot/r1_direction_twins.py')
BT = importlib.util.module_from_spec(spec); spec.loader.exec_module(BT)


def my_family(row):
    kind = TYPES.get(row.get('question_type'), 'unassigned:'+str(row.get('question_type')))
    if kind == 'direction' and row.get('facing') in ('toward', 'away'):
        return 'facing_pairs'
    if kind == 'counting' and row.get('count_kind') == 'total':
        return 'totals'
    return kind


def my_label(row):
    opts = row.get('student_input', {}).get('options', [])
    ans = str(row.get('answer', ''))
    hits = [o.split('.', 1)[1].strip() for o in opts if isinstance(o, str) and o.split('.', 1)[0].strip() == ans]
    return hits[0].lower() if len(hits) == 1 else None


def connect(p):
    return sqlite3.connect('file:'+str(p)+'?mode=ro&immutable=1', uri=True)


def work(span):
    lo, hi = span
    e, v = connect(ELIG), connect(V7)
    out = []
    for i, raw, target, cell, source, si, sha in e.execute(
            'SELECT i,row,target,cell,source,source_i,row_sha256 FROM rows WHERE i>=? AND i<? ORDER BY i', (lo, hi)):
        row = json.loads(raw)
        rec = dict(i=i, qid=row['qid'], cell=cell, source=source, source_i=si, sha_col=sha,
                   digest=digest(row), fam_tree=family(row, 'vqa'), fam_mine=my_family(row),
                   dataset=row.get('dataset'), scene=row.get('scene'), qtype=row.get('question_type'),
                   facing=row.get('facing'), pair_id=row.get('pair_id'), target_col=target,
                   label_row_keys=row.get('label_row_keys'))
        if source == 'store_v7':
            src = v.execute('SELECT row FROM rows WHERE i=?', (si,)).fetchone()
            rec['src_equal'] = src is not None and json.loads(src[0]) == row
        if rec['fam_tree'] in ('direction', 'facing_pairs'):
            rec['details'] = direction_details(row)
            rec['old_dims'] = BT.dimensions(row)
            rec['label'] = my_label(row)
            d7 = row.get('provenance', {}).get('sb_rowD7', {})
            rec['clause_edit'] = d7.get('clause_edit', {}).get('new_clause')
            rec['mapped_label'] = d7.get('mapped_label')
            rec['question'] = row['student_input']['question']
            rec['step_lines'] = [s for s in row['target'].splitlines()
                                 if s.startswith(('Step 2:', 'Standing at ', 'If I stood at '))]
        out.append(rec)
    e.close(); v.close()
    return out


if __name__ == '__main__':
    n = connect(ELIG).execute('SELECT count(*) FROM rows').fetchone()[0]
    step = 6000
    spans = [(a, min(a+step, n)) for a in range(0, n, step)]
    with Pool(7) as pool:
        recs = [r for chunk in pool.map(work, spans) for r in chunk]
    twins = {}
    with TWINS.open() as f:
        for line in f:
            r = json.loads(line); twins[r['qid']] = r
    for r in recs:
        if r['source'] == 'twins':
            t = twins.get(r['qid'])
            r['src_equal'] = t is not None and digest(t) == r['digest']
    (W/'rows.pkl').write_bytes(pickle.dumps(recs))
    print(len(recs), 'rows; twins file', len(twins), 'sha', hashlib.sha256(TWINS.read_bytes()).hexdigest()[:12])
