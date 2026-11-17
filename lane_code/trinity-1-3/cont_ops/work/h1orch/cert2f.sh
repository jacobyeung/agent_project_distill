export TZ=UTC; umask 077
O=/project/community/jjyeung/okh7
bad=0; for d in /project/community/jjyeung $O $O/i_1be16f28 $O/i_1be16f28/q_7b62108a $O/i_1be16f28/q_c492e8d1 $O/i_1be16f28/q_91f06d2e $O/i_1be16f28/q_f28a4d73 $O/i_1be16f28/q_6c18a2bf $O/i_1be16f28/q_6c18a2bf/o $O/i_1be16f28/q_6c18a2bf/o/native $O/x_3fdda0fb $O/x_3fdda0fb/o; do m=$(stat -c %a "$d"); echo "$m $d"; [ "$m" = 700 ] || bad=1; done
[ $bad = 0 ] || { echo "NOT_PRIVATE"; exit 4; }
echo ALL_PRIVATE
O=/project/community/jjyeung/okh7; B=$O/i_1be16f28
grep -q "\"status\":\"UNREVIEWED\"" $O/x_3fdda0fb/ANON_OK.json || { echo "ANON_OK not the placeholder"; exit 3; }
python3 - <<'P'
import json
from pathlib import Path
B=Path('/project/community/jjyeung/okh7/i_1be16f28')
p=B/'anon.json'; d=json.loads(p.read_text()); assert d['status']=='UNREVIEWED' and d['hits'] is None
q=B/'anon.json.unreviewed2'
if not q.exists(): q.write_text(p.read_text())
d.update(status='CLEAN',hits=0,reviewer='review_h1pkt2 (Devin Opus, content scan of upload d1279a8677c91e57, 2026-11-16T23:06Z; scan 32731d0b) and review_h1anon (Devin Opus, scan of new visible surfaces of fix6-8, 2026-11-17T04:34Z; 203 visible hits only in private BUN/q_6c18a2bf/o (native.log, ARKIT_* names), accepted as private under ORCH ruling 0439Z after mode check)',scan_sha256='3d096439977b8ce7d0eaf8811ee33773bf0e3ba7d8f681b78e8057132f7c4998',
 inherited=dict(count=52,ruling='orchestrator rulings 2028Z and 2309Z: compute-node names byte-identical from sealed kit 07ca49df accepted; no new visible name',
  items=['b/c.sh:11-13,115,117,151,174 and b/p0.sh:12 inherited R and part paths in argv','b/c.sh:102 base model dir in mv argv','b/c.sh:429 gcsput mode argv','b/c.sh:369-375 and b/r.sh:61 inherited env names']))
p.write_text(json.dumps(d,sort_keys=True,separators=(',',':')))
print('anon', d['status'], d['hits'], d['manifest_sha256'][:8], len(d['external']))
P
nice -n 19 bash $B/z.sh certify 2>&1 | grep -v ': OK$' | tail -n 15
echo certify_rc=${PIPESTATUS[0]}
ls -la $O/x_3fdda0fb/ANON_OK.json
