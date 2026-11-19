"""Seal the report, evidence and unchanged trainer provenance without Git."""
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'out'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
stamp=subprocess.check_output(['date','-u'],text=True).strip()
manifest=json.loads((OUT/'patches_b21/manifest.json').read_text())
application=manifest['_application'];tree=Path(application['tested_tree'])
for folder in ('patches','patches_b21'):
    for p in (OUT/folder).iterdir():
        assert p.read_bytes()==(ROOT/'out_round4'/folder/p.name).read_bytes(),p
files={str(p.relative_to(tree)):sha(p) for p in tree.rglob('*') if p.is_file()}
assert len(files)==application['candidate_source_files']
assert hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()==application['candidate_source_tree_sha256']
for folder in ('kit_profile','kit_timing'):
    for p in (OUT/folder).glob('*.py'): ast.parse(p.read_text(),filename=str(p))
    for p in (OUT/folder).glob('*.sh'): subprocess.run(['bash','-n',str(p)],check=True)
for name in ('REPORT.md','NOTE_FOR_TREE_REBUILD.md','SOURCE_NOTES.md','kit_profile/README.md','kit_timing/README.md'):
    p=OUT/name;s=p.read_text()
    for target in re.findall(r'\]\(([^)]+)\)',s):
        if '://' not in target:
            assert (p.parent/target.split('#')[0]).is_file(),(name,target)
    assert '30–60 minutes' not in s
for name in ('REPORT.md','NOTE_FOR_TREE_REBUILD.md'):
    s=(OUT/name).read_text()
    assert s.startswith('VERDICT: DONE ')
    assert '## Review round 4: finding -> fix -> test' in s
    for phrase in ('880.158','12:55:19','50–75 minutes','2 ×','1.00','updates 2–21',
                   'tests.test_so_round3','tests.test_gx_carrier.GXPTests.test_two_rank_gxp_first_batch_forward_backward',
                   'tests.test_gx_carrier.GXTests.test_two_rank_fsdp_replicas_checkpoint_and_exports'):
        assert phrase in s,(name,phrase)
    assert 'Every emitted grid must fit `[32,20,26]`' not in s
checks=json.loads((OUT/'evidence/round4_checks.json').read_text())
assert len(checks)==12 and all(c['accepted'] for c in checks)
dedicated=[c for c in checks if c['kind'] not in ('existing','related')]
count=sum(int(re.search(r'Ran (\d+) test',c['summary'][0])[1]) for c in dedicated)
assert count==79
assert 'FAILED (failures=11, errors=1)' in (OUT/'evidence/round4_kits_before.txt').read_text()
assert 'FAILED (failures=1)' in (OUT/'evidence/round4_mixed_control.txt').read_text()
assert '\nOK\n' in (OUT/'evidence/round4_round4_kits.txt').read_text()
assert (OUT/'evidence/coordinator_b21_31.txt').read_bytes()==(ROOT/'work/round3_b21_gloo_by_coordinator.txt').read_bytes()
usage=int(subprocess.check_output(['du','-sb',str(ROOT)],text=True).split()[0])
assert usage<3_000_000_000
(ROOT/'work/STATUS.md').write_text(
    'Updated '+stamp+'. Started 2026-11-19 13:27:56 UTC; deadline 14:57:56 UTC.\n\n'
    'VERDICT: DONE. All ten review findings are addressed. out_round4 preserves the input delivery. '
    'Both reports begin VERDICT: DONE and include Review round 4: finding -> fix -> test.\n\n'
    'The four handed-over trainer patches and manifests remain byte-identical. Fresh zero-fuzz/offset '
    'replay matches all 22 touched files; the full 949-file candidate source digest is unchanged. '
    'Coordinator gloo already passed 31 tests in 880.158 s at 2026-11-19 12:55:19 UTC.\n\n'
    'Local dedicated results: 79 cases, 78 passes and one skip. The broader 91- and 55-case suites '
    'reproduce exactly eight known baseline failure entries. Twelve defect regressions fail against '
    'the snapshot and pass on the delivery. Mixed fallback passes on the unchanged trainer; its '
    'all-fallback mutation fails. Complete commands and outputs are in out/evidence/round4_*.\n\n'
    'Kits now accept both grid orientations under t<=32 and h*w<=520 and report observed grids; '
    'use a fixed pooled per-rank replay multiplier 2; write and consume the trainer-merged receipt; '
    'publish success sidecars only after validation; and specify numeric continuation thresholds. '
    'Lossless JSON escaping preserves receipt values without literal model words. Both reports '
    'state current gate status, explicit replay variables, optional fallback field and 50–75 minute '
    'replay estimate. Mirrored portrait records are at lines 702/706/710/714 (review offsets +8).\n\n'
    'No production GPU, torchvision audit, replay or performance measurement was run. These remain '
    'host admission checks. No Git, SSH, deletion or external job was used. Workspace size measured '
    'before final inventory: '+str(usage)+' bytes, below 3 GB.\n')
messages=[stamp,
    'PATCH_BYTES_UNCHANGED: four diffs and both manifests match out_round4',
    'TRAINER_SOURCE_UNCHANGED: 949 files; '+application['candidate_source_tree_sha256'],
    'FINAL_SYNTAX_AND_LINKS_PASS: all kit Python/shell files and report links',
    'LOCAL_GATES_PASS: 79 dedicated cases, 78 passes, one skip; eight unchanged baseline failure entries',
    'REGRESSIONS_PASS: 12 snapshot failures become passes; mixed fallback passes and mutation fails',
    'COORDINATOR_GATE_PASS: 31 tests in 880.158 s, EXIT=0, 2026-11-19 12:55:19 UTC',
    'WORKSPACE_BYTES: '+str(usage), 'EXIT=0']
(OUT/'evidence/round4_final.txt').write_text('\n'.join(messages)+'\n')
paths=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name!='ARTIFACTS.json')
previous=json.loads((OUT/'ARTIFACTS.json').read_text())
extras={ROOT/'work'/Path(name).name for name in previous['artifacts'] if name.startswith('../work/')}
extras.update(ROOT/'work'/name for name in ('test_round4_kits.py','test_round4_mixed.py',
    'run_round4_checks.py','verify_round4.py','finalize_round4.py','STATUS.md','round3_b21_gloo_by_coordinator.txt'))
paths.extend(sorted(extras))
records={str(p.relative_to(OUT)) if p.is_relative_to(OUT) else '../work/'+p.name:
         dict(bytes=p.stat().st_size,sha256=sha(p)) for p in paths}
inventory=dict(verified_utc=stamp,review_round=4,verdict='DONE',base_pin=application['base_pin'],
    candidate_source_tree_sha256=application['candidate_source_tree_sha256'],trainer_patches_changed=False,
    snapshot='out_round4',local_dedicated_cases=79,local_passes=78,local_skips=1,baseline_failure_entries=8,
    coordinator_gloo='31 tests OK in 880.158 s, EXIT=0, 2026-11-19 12:55:19 UTC; unchanged handed-over trainer bytes',
    gpu_kits='not run',workspace_bytes=usage,artifacts=records)
(OUT/'ARTIFACTS.json').write_text(json.dumps(inventory,indent=2)+'\n')
print('\n'.join(messages))
print('ARTIFACTS_HASHED: '+str(len(records)))
