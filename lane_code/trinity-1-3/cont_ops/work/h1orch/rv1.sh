export TZ=UTC; umask 077
O=/project/community/jjyeung/okh7; B=$O/i_1be16f28
test -e $O/x_4b3114cf && { echo "KH exists"; exit 3; }
python3 - <<'P'
import json,hashlib
from pathlib import Path
B=Path('/project/community/jjyeung/okh7/i_1be16f28')
p=B/'review.json'; d=json.loads(p.read_text())
assert d['verdict']=='PENDING' and d['reviewer'] is None
ids=json.loads((B/'ids.json').read_text())
d.update(verdict='PASS',reviewer='review_h1pkt (Devin Opus cross-family refute, GO AFTER FIXES 2026-11-16T20:27Z; fixes gated per orchestrator ruling 2028Z) and review_h1pkt2 (Devin Opus, fixes 3-5 GO 2026-11-16T23:06Z)',
 attestation='Independent reviews of this code tree and runtime changes: REVIEW_VERDICT_H1PKT.md and REVIEW_VERDICT_H1PKT2.md; faithful gate PASS 0.99817 (gate.json). CPU fixtures do not establish production admission.',
 evidence=dict(gate_json_sha256=hashlib.sha256((B/'gate.json').read_bytes()).hexdigest()))
p.write_text(json.dumps(d,sort_keys=True,separators=(',',':')))
print(d['verdict'], d['config_sha256'][:8], d['admission_contract_sha256'][:8], d['source_revision'][:16])
P
nohup setsid nice -n 19 ionice -c3 bash $B/z.sh derive > $O/t_c94bbc4e.z.log 2>&1 < /dev/null &
echo started derive pid $!
