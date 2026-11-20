import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
# Preserve the standard selected-build artifact names and publish each independently.
for n in NAMES:
 p=kit(n)/'b/ep.py';s=p.read_text().replace('    return result\n\n\ndef publish_artifacts', '''    primary=root/'dr/p/q/selection'
    if not primary.is_dir():primary=root/'p/q/selection'
    for filename in ('materialization.json','receipt.json'):
        result.append((filename,primary/filename))
    refresh=root/'dr/p/i/pool/r.json'
    if not refresh.is_file():refresh=root/'p/i/pool/r.json'
    result.append(('refresh.json',refresh))
    return result


def publish_artifacts''');replace(p,s)
 p=kit(n)/'b/pl.py';s=p.read_text().replace("        closure(p_config['code'],'P.config.code')", "        closure(p_config['code'],'P.config.code')\n        closure(p_config.get('s1_route_policy',{}),'P.config.s1_route_policy')");replace(p,s)
# One explicit signature keeps the environment-name scanner fully resolved.
seals={n:reseal(kit(n)) for n in NAMES};J.write(D/'SEALS.json',seals)
# Retained fabricated review fixture has authenticated bytes in the input package.
p=D/'review_tests.py';s=p.read_text().replace('L/"work/build24m4d/arming_final/routing_selection.json"','L/"work/build24m4f/review_negatives/reviewer_fabricated_selection_probe_selection.json"').replace('L/"work/build24m4d/arming_final/db_bytes.json"','L/"work/build24m4f/review_negatives/reviewer_fabricated_selection_probe_db.json"');replace(p,s)
p=D/'offline.py';s=p.read_text().replace('assert len(records)==3','assert len(records)==6').replace('assert len(records)==4','assert len(records)==7');replace(p,s)
# Identify the write incident precisely; do not touch those external files again.
paths=[W/'w24/work/build21/inputs/config.json',W/'w24/work/build21/inputs/kit_config.json',W/'w24/work/build21/kits/q/k/s.json']
v=[]
for p in paths:v.append(dict(path=str(p),sha256=J.sha(p),bytes=p.stat().st_size,mtime_ns=p.stat().st_mtime_ns))
old_sums={n:h for h,n in (line.split('  ',1) for line in (W/'w24/work/build21/kits/q/SHA256SUMS.txt').read_text().splitlines())}
J.write(D/'WRITE_BOUNDARY_INCIDENT.json',dict(cause='Inherited resolver600 test imported work/build21/kit.py, which runs builder work at import time',files_rewritten=v,k_s_matches_existing_seal=v[-1]['sha256']==old_sums['k/s.json'],failure_log='work/build24m4h/resolver600_tests.log',containment='run.sh now mounts the host read-only and grants writes only to w24h; resolver600 uses the local side-effect-free kit helper',external_restore_attempted=False))
print('FINAL RUNTIME SEALS',seals)
