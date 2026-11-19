#!/usr/bin/env python3
"""Form classifier and per-row membership table for the counting fix (lane count_diag, 2026-11-18).

Reads store v7 read-only (sqlite ?immutable=1), the pinned REMOVE list n.json and A2 v3's CHANGES.jsonl; writes, under --out:
  MEMBERSHIP_V7_COUNTING.tsv  one line per object_counting and first_seen_frame row of v7, with its cell, trace form,
                              list entry and repeat counts, and membership in n.json, B1, B1_keepD0totals, A and the restore set
  REPEATS_BY_FAMILY.json      lists, entries, repeated entries and rows with a repeat, by family and list length
  COUNT_FIX_REMOVE_B1.jsonl, COUNT_FIX_REMOVE_B1_keepD0totals.jsonl, COUNT_FIX_REMOVE_A.jsonl  regenerated (sealed Removals
                              format of n.json); their sha256 must equal the posted files
Rules:
  cell      totals if the row carries count_kind (the production loader's totals cell), first_seen for first_seen_frame,
            otherwise counting (171377's type_mix populations equal these sets: VERIFY_FIX.txt)
  form      TOTALS for the totals cell; FS_LIST if the think cites a first-seen list (LIST_RE); PROC if it gives the
            procedure sentence ("count it once" / "count each once") and no list; FIRST_SEEN for first_seen_frame rows;
            _REGION is appended when an entry carries a region word "(left|middle|right)"
  repeats   per list (the text after a first-seen phrase up to the line end, split on ';'), entries minus distinct entries
  B1        every FS_LIST or TOTALS row not already in n.json
  B1_keepD0totals  B1 without the D0 gap totals (pools rows_rebuild_d0_*)
  A         every TOTALS row and every FS_LIST row outside the restore set, not already in n.json
  restore   the object_counting rows of A2 v3 CHANGES.jsonl (D0 v5 target restored in plan A)
"""
import argparse, collections, hashlib, json, os, re, sqlite3

V7 = '/scratch/jjyeung/orch_n30/rows_r1/out/a2_vqa_v7'
N_JSON = '/scratch/jjyeung/orch_n30/r1_ops/work/snap_fac07052/out/records/n.json'
CHANGES = '/scratch/jjyeung/orch_n30/rows_a2/out/a2_vqa_v3/CHANGES.jsonl'
LIST_RE = re.compile(r'(?:at its first appearance|by the frame where it first appears|by first appearance|using its first-seen frame|first seen in)\s*:')
LIST_CAP = re.compile(r'(?:at its first appearance|by the frame where it first appears|by first appearance|using its first-seen frame|first seen in)\s*:\s*([^\n]*)')
PROC_RE = re.compile(r'count (?:it|each) once')
REGION_RE = re.compile(r'\((?:left|middle|right)\)')
REASON = 'count_diag_first_seen_list_form'


def sha_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def lists_of(target):
    out = []
    for m in LIST_CAP.finditer(target):
        ents = [e.strip(' .') for e in m.group(1).split(';') if e.strip(' .')]
        if ents:
            out.append(ents)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--store', default=V7)
    ap.add_argument('--n-json', default=N_JSON)
    ap.add_argument('--changes', default=CHANGES)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rem = {json.loads(l)['row_key'] for l in open(a.n_json) if l.strip()}
    restore = {json.loads(l)['qid'] for l in open(a.changes) if json.loads(l)['question_type'] == 'object_counting'}
    ranges = json.load(open(os.path.join(a.store, 'FAMILY_INDEX_RANGES.json')))['families']
    con = sqlite3.connect('file:%s?immutable=1' % os.path.join(a.store, 'vqa', 'rows.sqlite'), uri=True)
    rows = []
    for fam in ('object_counting', 'first_seen_frame'):
        for lo, hi in ranges[fam]:
            for i, raw in con.execute('select i,row from rows where i between ? and ? order by i', (lo, hi)):
                r = json.loads(raw)
                t = r.get('target') or ''
                if fam == 'first_seen_frame':
                    cell, form = 'first_seen', 'FIRST_SEEN'
                elif 'count_kind' in r:
                    cell, form = 'totals', 'TOTALS'
                else:
                    cell = 'counting'
                    form = 'FS_LIST' if LIST_RE.search(t) else ('PROC' if PROC_RE.search(t) else 'OTHER')
                if form in ('FS_LIST', 'TOTALS') and REGION_RE.search(t):
                    form += '_REGION'
                L = lists_of(t) if form != 'FIRST_SEEN' else []
                ent = sum(len(x) for x in L)
                rep = sum(len(x) - len(set(x)) for x in L)
                mrun = 0
                for x in L:
                    run = 1
                    mrun = max(mrun, 1)
                    for p, q in zip(x, x[1:]):
                        run = run + 1 if p == q else 1
                        mrun = max(mrun, run)
                q = r['qid']
                base = form.replace('_REGION', '')
                in_n = q in rem
                b1 = (base in ('FS_LIST', 'TOTALS')) and not in_n
                pool = r.get('pool') or ''
                b1k = b1 and not (base == 'TOTALS' and pool.startswith('rows_rebuild_d0_'))
                ina = (base == 'TOTALS' or (base == 'FS_LIST' and q not in restore)) and not in_n
                rows.append(dict(i_v7=i, qid=q, pool=pool, question_type=r.get('question_type'), cell=cell, form=form,
                                 n_lists=len(L), n_entries=ent, n_repeated_entries=rep, has_repeat=int(rep > 0), max_run=mrun,
                                 answer=r.get('answer'), in_n_json=int(in_n), in_B1=int(b1), in_B1_keepD0totals=int(b1k),
                                 in_A=int(ina), in_restore=int(q in restore),
                                 scene='%s/%s' % (r.get('dataset'), r.get('scene')),
                                 target_sha256=hashlib.sha256(t.encode()).hexdigest()))
    cols = ['i_v7', 'qid', 'pool', 'question_type', 'cell', 'form', 'n_lists', 'n_entries', 'n_repeated_entries', 'has_repeat',
            'max_run', 'answer', 'in_n_json', 'in_B1', 'in_B1_keepD0totals', 'in_A', 'in_restore', 'scene', 'target_sha256']
    with open(os.path.join(a.out, 'MEMBERSHIP_V7_COUNTING.tsv'), 'w') as f:
        f.write('\t'.join(cols) + '\n')
        for x in rows:
            f.write('\t'.join(str(x[c]) for c in cols) + '\n')
    fam = lambda x: (x['pool'] if not x['pool'].startswith('rows_rebuild_d0_') else 'd0_gaps') + ':' + x['form']
    rep = collections.defaultdict(lambda: dict(rows=0, rows_after_n_json=0, lists=0, entries=0, repeated_entries=0, rows_with_repeat=0,
                                               by_list_length={}))
    for x in rows:
        d = rep[fam(x)]
        d['rows'] += 1
        if x['in_n_json']:
            continue
        d['rows_after_n_json'] += 1
        d['lists'] += x['n_lists']; d['entries'] += x['n_entries']; d['repeated_entries'] += x['n_repeated_entries']
        d['rows_with_repeat'] += x['has_repeat']
        if x['n_lists'] == 1:
            k = str(min(x['n_entries'], 6)) if x['n_entries'] < 6 else '6+'
            b = d['by_list_length'].setdefault(k, [0, 0])
            b[0] += x['has_repeat']; b[1] += 1
    for d in rep.values():
        d['repeated_entry_share'] = round(d['repeated_entries'] / d['entries'], 4) if d['entries'] else None
        d['by_list_length'] = {k: '%d of %d repeat' % tuple(v) for k, v in sorted(d['by_list_length'].items())}
    json.dump(rep, open(os.path.join(a.out, 'REPEATS_BY_FAMILY.json'), 'w'), indent=1, sort_keys=True)

    def write(name, key):
        sel = sorted((x for x in rows if x[key]), key=lambda x: x['i_v7'])
        p = os.path.join(a.out, name)
        with open(p, 'w') as f:
            for x in sel:
                f.write(json.dumps({'pool': x['pool'], 'question_type': x['question_type'], 'reason': REASON,
                                    'row_key': x['qid'], 'scene': x['scene']}, sort_keys=True, separators=(',', ':')) + '\n')
        return len(sel), sha_file(p)
    summ = dict(store=os.path.join(a.store, 'vqa', 'rows.sqlite'), n_json=a.n_json, n_json_sha256=sha_file(a.n_json),
                changes_sha256=sha_file(a.changes), rows=len(rows),
                forms=collections.Counter(fam(x) for x in rows),
                cells_after_n_json={c: sum(1 for x in rows if x['cell'] == c and not x['in_n_json']) for c in ('counting', 'totals', 'first_seen')},
                remaining_after_B1={c: sum(1 for x in rows if x['cell'] == c and not x['in_n_json'] and not x['in_B1']) for c in ('counting', 'totals')},
                remaining_forms_after_B1=collections.Counter(x['form'] for x in rows if x['cell'] in ('counting', 'totals') and not x['in_n_json'] and not x['in_B1']),
                B1=write('COUNT_FIX_REMOVE_B1.jsonl', 'in_B1'),
                B1_keepD0totals=write('COUNT_FIX_REMOVE_B1_keepD0totals.jsonl', 'in_B1_keepD0totals'),
                A=write('COUNT_FIX_REMOVE_A.jsonl', 'in_A'),
                membership_sha256=sha_file(os.path.join(a.out, 'MEMBERSHIP_V7_COUNTING.tsv')))
    json.dump(summ, open(os.path.join(a.out, 'CLASSIFY_SUMMARY.json'), 'w'), indent=1, sort_keys=True)
    print(json.dumps(summ, indent=1, sort_keys=True))


if __name__ == '__main__':
    main()
