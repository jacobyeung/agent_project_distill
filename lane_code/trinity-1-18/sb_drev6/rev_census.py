"""Independent census of v7 direction rows and recomputation of the toward/away twin gate."""
import collections as C, hashlib, json, pickle, re, sqlite3, sys
from pathlib import Path

DB = '/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite'
OUT = Path(__file__).resolve().parent / 'work'
OUT.mkdir(exist_ok=True)
SWAP = {'left': 'right', 'right': 'left', 'front': 'back', 'back': 'front'}


def opts(r):
    o = {}
    for s in r['student_input']['options']:
        m = re.fullmatch(r'([A-Z])\.\s*(.+)', s)
        o[m[1]] = m[2].strip().lower()
    return o


def clause(q):
    ql = q.lower()
    if 'opposite' in ql:
        return 'opposite'
    if re.search(r'away from|with my back to|back turned to|back to the', ql):
        return 'away'
    return 'toward'


def opening(t):
    first = t.removeprefix('<think>\n').split('\n', 1)[0]
    return 'Seen' if first.startswith('Seen:') else 'Step 1' if first.startswith('Step 1:') else 'OTHER'


def main():
    con = sqlite3.connect('file:' + DB + '?mode=ro&immutable=1', uri=True)
    qids, cids = set(), set()
    dirrows = {}
    for i, raw in con.execute('select i,row from rows order by i'):
        r = json.loads(raw)
        qids.add(r['qid'])
        if r.get('candidate_id'):
            cids.add(r['candidate_id'])
        if r.get('question_type', '').startswith('object_rel_direction_'):
            dirrows[i] = dict(i=i, qid=r['qid'], fam=r['question_type'].rsplit('_', 1)[1], pool=r['pool'],
                              facing=r.get('facing'), pair=r.get('pair_id'), op=opening(r['target']),
                              cl=clause(r['student_input']['question']), label=opts(r)[r['answer']],
                              answer=r['answer'], options=r['student_input']['options'], scene=r['scene'],
                              dataset=r['dataset'], q=r['student_input']['question'],
                              src=r.get('provenance', {}).get('source'), sha=hashlib.sha256(raw.encode()).hexdigest(),
                              frames=hashlib.sha256(json.dumps(r['student_input']['frame_indices']).encode()).hexdigest())
    byqid = {m['qid']: m for m in dirrows.values()}
    cen = C.Counter((m['op'], m['cl'], m['fam'], m['facing']) for m in dirrows.values())
    print('direction rows', len(dirrows), 'qids', len(qids), 'cids', len(cids))
    for k, v in sorted(cen.items(), key=str):
        print(' ', k, v)
    # Gate: every v7 row whose pair_id names a toward mate in the same family.
    gate = C.Counter(); dis = C.Counter(); multi = C.Counter()
    for m in dirrows.values():
        if m['cl'] == 'toward' or not m['pair']:
            continue
        t = byqid.get(m['pair'])
        if t is None or t['cl'] != 'toward':
            gate['no_toward_mate', m['cl'], m['fam']] += 1
            continue
        lit = '-'.join(SWAP[x] for x in t['label'].split('-')) if t['label'] != 'back' else 'front'
        gate[m['cl'], m['fam']] += 1
        if lit != m['label']:
            dis[m['cl'], m['fam']] += 1
        # Unique mapping: exactly one option text equals the literal half turn.
        n = sum(v == lit for v in opts_list(m['options']))
        multi[m['cl'], m['fam'], n] += 1
    print('pairs', dict(gate)); print('literal disagreements', dict(dis)); print('options equal to literal', dict(multi))
    pickle.dump(dict(qids=qids, cids=cids, dirrows=dirrows), open(OUT / 'census.pkl', 'wb'))


def opts_list(options):
    return [re.fullmatch(r'([A-Z])\.\s*(.+)', s)[2].strip().lower() for s in options]


if __name__ == '__main__':
    main()
