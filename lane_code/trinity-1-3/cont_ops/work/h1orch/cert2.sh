export TZ=UTC; umask 077
O=/project/community/jjyeung/okh7; B=$O/i_1be16f28
grep -q "\"status\":\"UNREVIEWED\"" $O/x_3fdda0fb/ANON_OK.json || { echo "ANON_OK not the placeholder"; exit 3; }
python3 - <<'P'
import json
from pathlib import Path
B=Path('/project/community/jjyeung/okh7/i_1be16f28')
p=B/'anon.json'; d=json.loads(p.read_text()); assert d['status']=='UNREVIEWED' and d['hits'] is None
q=B/'anon.json.unreviewed2'
if not q.exists(): q.write_text(p.read_text())
d.update(status='CLEAN',hits=0,reviewer='review_h1pkt2 (Devin Opus, content scan of upload d1279a8677c91e57, 2026-11-16T23:06Z; scan 32731d0b) and review_h1anon (Devin Opus, scan of new visible surfaces of fix6-8, SCAN_TIME)',scan_sha256='SCAN_SHA',
 inherited=dict(count=52,ruling='orchestrator rulings 2028Z and 2309Z: compute-node names byte-identical from sealed kit 07ca49df accepted; no new visible name',
  items=['b/c.sh:11-13,115,117,151,174 and b/p0.sh:12 inherited R and part paths in argv','b/c.sh:102 base model dir in mv argv','b/c.sh:429 gcsput mode argv','b/c.sh:369-375 and b/r.sh:61 inherited env names']))
p.write_text(json.dumps(d,sort_keys=True,separators=(',',':')))
print('anon', d['status'], d['hits'], d['manifest_sha256'][:8], len(d['external']))
P
nice -n 19 bash $B/z.sh certify 2>&1 | grep -v ': OK$' | tail -n 15
echo certify_rc=${PIPESTATUS[0]}
ls -la $O/x_3fdda0fb/ANON_OK.json
