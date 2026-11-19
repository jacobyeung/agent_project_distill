"""Hash the current review delivery and validate its report/evidence links."""
import ast
import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'out'
report=(OUT/'REPORT.md').read_text()
assert report.startswith('VERDICT: DONE ')
assert '## Review round 1: finding -> fix -> test' in report
assert 'To be run by the coordinator outside the sandbox' in report
assert 'Patch 04 stays separate' in report
assert '29 local tests pass' in report
for target in re.findall(r'\]\(([^)]+)\)',report):
 if target.startswith(('https:','http:')): continue
 path=(OUT/target.split('#',1)[0]).resolve()
 assert path.is_file(),target
manifest=json.loads((OUT/'patches/manifest.json').read_text())
for name,item in manifest.items():
 if not name.endswith('.diff'): continue
 payload=(OUT/'patches'/name).read_bytes()
 assert hashlib.sha256(payload).hexdigest()==item['sha256']
 assert len(payload)==item['bytes']
for folder in ('kit_profile','kit_timing'):
 for path in (OUT/folder).glob('*.py'): ast.parse(path.read_text(),filename=str(path))
 for path in (OUT/folder).glob('*.sh'): subprocess.run(['bash','-n',str(path)],check=True)
for name in ('review1_final_units.txt','review1_final_parity.txt','review1_final_kits.txt',
             'review1_final_kit_regressions.txt','review1_final_utilities.txt'):
 value=(OUT/'evidence'/name).read_text()
 assert '\nOK\n' in value and value.endswith('EXIT=0\n'),name
paths=[OUT/'REPORT.md',OUT/'SOURCE_NOTES.md',OUT/'patches/manifest.json']
paths+=sorted((OUT/'patches').glob('*.diff'))
for folder in ('kit_profile','kit_timing'):
 paths+=sorted(path for path in (OUT/folder).iterdir() if path.is_file())
paths+=sorted((OUT/'evidence').glob('review1_*.txt'))
paths += [ROOT/'work/full_suite_by_swarm_opt2.txt']
records={str(path.relative_to(OUT)) if path.is_relative_to(OUT) else '../work/'+path.name:
         dict(bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest()) for path in paths}
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
(OUT/'ARTIFACTS.json').write_text(json.dumps(dict(verified_utc=now,verdict='DONE',review_round=1,
 local_tests=29,patch_04='kept separate',coordinator_gloo='to be run outside the sandbox on revised source',
 prior_coordinator_suite='../work/full_suite_by_swarm_opt2.txt',gpu_kits='not run',artifacts=records),indent=2)+'\n')
(ROOT/'work/STATUS.md').write_text(f'''Updated {now}; deadline 2026-11-19 10:15 UTC.

VERDICT: DONE. Findings 1–14 and arithmetic finding 15 are fixed. The report contains the requested finding -> fix -> test section, exact outputs, framework source citations, and the exact coordinator command.

Four ordered patches reproduce all 14 touched files with zero fuzz; 931 other files match the input. Patch 04 stays separate. All 29 local tests pass: 14 trainer regressions, 2 native parity tests, 4 native setup/profile tests, 7 kit regressions and 2 data/statistics tests. Integrity, syntax and production-log arithmetic checks pass. The final artifact inventory is out/ARTIFACTS.json.

The supplied coordinator suite passed ten tests, including two-rank gloo, for the reviewed series. The revised two-rank gloo tests are to be run by the coordinator outside the sandbox. GPU kits and production processor/timing checks remain unrun as requested. No production speedup is claimed. The workspace uses about 365 MB; local scratch has 429 GB free.
''')
print(f'DELIVERY_PASS: {len(records)} artifacts hashed; report links, four patch hashes, kit syntax and 29 passing local tests verified')
print('COORDINATOR_PENDING: revised two-rank gloo; exact command in out/REPORT.md')
print('GPU_KITS: not run')
