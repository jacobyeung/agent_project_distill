export TZ=UTC; umask 077
O=/project/community/jjyeung/okh7; B=$O/i_1be16f28
test -e $O/x_3fdda0fb && { echo "KH exists"; exit 3; }
python3 - <<'P'
import json,hashlib
from pathlib import Path
B=Path('/project/community/jjyeung/okh7/i_1be16f28')
p=B/'review.json'; d=json.loads(p.read_text())
assert d['verdict']=='PENDING' and d['reviewer'] is None
ids=json.loads((B/'ids.json').read_text())
d.update(verdict='PASS',reviewer='review_h1pkt (Devin Opus, GO AFTER FIXES 2026-11-16T20:27Z, fixes gated per ruling 2028Z), review_h1pkt2 (Devin Opus, fixes 3-5 GO 2026-11-16T23:06Z) and review_h1sel (Devin Opus, selection regeneration tool + EQUAL pin, GO 2026-11-17T04:09Z)',
 attestation='Independent reviews: REVIEW_VERDICT_H1PKT.md, REVIEW_VERDICT_H1PKT2.md, REVIEW_VERDICT_H1SEL.md (disk-plan fix FIX6, routing selection regenerated EQUAL e48ab85b and pinned FIX8, per orchestrator ruling 0211Z); faithful gate PASS (gate.json). Production CPU preparation proof follows before submission.',
 evidence=dict(gate_json_sha256=hashlib.sha256((B/'gate.json').read_bytes()).hexdigest()))
p.write_text(json.dumps(d,sort_keys=True,separators=(',',':')))
print(d['verdict'], d['config_sha256'][:8], d['admission_contract_sha256'][:8], d['source_revision'][:16])
P
nohup setsid nice -n 19 ionice -c3 bash $B/z.sh derive > $O/t_og8a.z.log 2>&1 < /dev/null &
echo started derive pid $!
