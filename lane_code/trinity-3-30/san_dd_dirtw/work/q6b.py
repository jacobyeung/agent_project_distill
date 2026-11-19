"""Q6b: do dev-S1 rooms or item ids occur in store v7 training rows?  qids and scenes of all direction rows (json_extract, by primary key, 200 per query); ScanNet++ scene ids from size rows' raster field."""
import sys, json, sqlite3, re, collections
sys.path.insert(0, '/scratch/jjyeung/orch_n30/san_dd_dirtw/work'); from tw_lib import K, T
F = json.load(open('/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/FAMILY_INDEX_RANGES.json'))['families']
con = sqlite3.connect('file:/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/vqa/rows.sqlite?mode=ro', uri=True)
dids = [i for t in T for a, b in F[t] for i in range(a, b + 1)]
qids = set(); scenes = collections.Counter()
for k in range(0, len(dids), 200):
    for q, s in con.execute("select json_extract(row,'$.qid'), json_extract(row,'$.scene') from rows where i in (%s)" % ','.join(map(str, dids[k:k + 200]))):
        qids.add(q); scenes[s] += 1
sids = [i for a, b in F['object_size_estimation'] for i in range(a, b + 1)]; rasters = set()
for k in range(0, len(sids), 200):
    for (ra,) in con.execute("select json_extract(row,'$.retrace_a2.raster') from rows where i in (%s)" % ','.join(map(str, sids[k:k + 200]))):
        if ra: rasters.add(ra)
print('direction rows', len(dids), 'distinct qids', len(qids), 'distinct scenes', len(scenes), '; size-row rasters', len(rasters), 'e.g.', sorted(rasters)[:2])
dev = K.direct('R1', 200, 'dev-S1'); r0 = K.direct('R1', 200, 'R0-dev')
dir_dev = [r for r in dev if r['type'] in T]
print('dev-S1 direction item ids that are training qids:', sum(r['id'] in qids for r in dir_dev), 'of', len(dir_dev), '; all dev-S1 ids:', sum(r['id'] in qids for r in dev), 'of', len(dev))
print('R0-dev ids that are training qids:', sum(r['id'] in qids for r in r0), 'of', len(r0))
rs = {re.sub(r'^scannetppv2__|\.npz$', '', x) for x in rasters}
d2 = {r['room'].split('/')[1] for r in dev if r['room'].startswith('d2/')}
print('dev-S1 ScanNet++ rooms', len(d2), 'found among size-row raster scenes:', len(d2 & rs), '; R0-dev rooms found:', len({r['room'] for r in r0} & rs))
qn = collections.Counter(re.sub(r'\d', '9', q)[:12] for q in qids); print('training qid formats', qn.most_common(4))
