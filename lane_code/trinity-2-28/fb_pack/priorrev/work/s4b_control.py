"""Positive control for s4_legal: the same matcher must hit rows of the full v7 store
that the filters removed; also check division held-out QIDs and the tree's own matchers."""
import json, re, sqlite3, sys
from collections import Counter
from pathlib import Path
import s4_legal as L

W = Path(__file__).resolve().parent
sys.path.insert(0, str(W/'new'))


def main():
    import pickle
    recs = pickle.loads((W/'rows.pkl').read_bytes())
    kept = {r['qid'] for r in recs}
    div = json.loads(L.F['division'].read_text())
    hq = set(div.get('heldout_qids') or [])
    out = dict(division_heldout_scenes=div.get('heldout_scenes'), division_heldout_qids=len(hq),
               division_heldout_groups=len(div.get('heldout_group_ids') or []))
    out['kept_in_division_heldout_qids'] = len(kept & hq)
    expanded, natives, venue = L.build({})
    tok2nat = {}
    for d, sc in natives:
        for t in L.tokens(d, sc):
            tok2nat[(d, t)] = (d, sc)
    v7 = sqlite3.connect('file:'+str(L.FB/'ro/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite')+'?mode=ro&immutable=1', uri=True)
    hits = Counter(); unresolved = 0; n = 0
    for (raw,) in v7.execute('SELECT row FROM rows ORDER BY i'):
        row = json.loads(raw); n += 1
        d = L.DS.get(str(row.get('dataset')).casefold(), row.get('dataset'))
        key = (d, row.get('scene'))
        nat = tok2nat.get(key) if re.fullmatch(r'v[0-9a-f]{12}', str(row.get('scene'))) else key
        unresolved += nat is None
        keys = {key} | ({nat} if nat else set())
        if nat and L.room(*nat): keys.add(L.room(*nat))
        if nat in venue: keys.add(venue[nat])
        kept_flag = row['qid'] in kept
        for name, e in expanded.items():
            if keys & e:
                hits[name, 'kept' if kept_flag else 'removed'] += 1
        if row['qid'] in hq:
            hits['division_heldout_qid', 'kept' if kept_flag else 'removed'] += 1
    out['v7_rows'] = n; out['v7_unresolved'] = unresolved
    out['v7_hits'] = {'|'.join(k): v for k, v in sorted(hits.items())}
    # tree's own matchers on all kept direction/facing rows
    from student_pilot.s1_exclusions import Exclusions
    from student_pilot.r0_exclusion import Reserve
    pin = lambda p: dict(path=str(p), sha256=L.sha(p))
    ex = Exclusions(pin(L.F['dev_s1']), pin(L.F['bench']))
    rs = Reserve(L.F['r0'])
    e = sqlite3.connect('file:'+str(L.FB/'prior2b/work/source/eligible_vqa.sqlite')+'?mode=ro&immutable=1', uri=True)
    tree = Counter()
    for (raw,) in e.execute("SELECT row FROM rows"):
        row = json.loads(raw)
        m = ex.matches(row)
        tree['dev_match'] += m['dev']; tree['bench_match'] += m['benchmark']
        tree['r0_match'] += bool(rs.matches(row)); tree['rows'] += 1
    out['tree_matchers_on_kept'] = dict(tree)
    (W/'S4B_CONTROL.json').write_text(json.dumps(out, indent=1) + '\n')
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
