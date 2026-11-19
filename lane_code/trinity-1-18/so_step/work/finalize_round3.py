"""Validate delivery bytes, commands, docs and source scope; retain the artifact inventory."""
import ast
import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'out'
TREE=ROOT/'work/b21_final/work/tree_r1'
REPLAY=ROOT/'work/round3_replay'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=OUT/'kit_timing/README.md';s=p.read_text().replace('`--full-plan` remains available to inspect every supplied plan but is not required for a complete epoch.', '`--full-plan` audits every supplied plan; the acceptance plan contains 10 updates.');p.write_text(s)
p=OUT/'SOURCE_NOTES.md';s=p.read_text().replace('All paths below refer to the supplied build-20 source or the installed CPU environment, not an inferred production checkout.', 'The `T` citations name the supplied source used for the timing analysis. Build-21 sections name their input and tested roots explicitly; `E` always names the installed CPU environment. None denotes an inferred production checkout.');p.write_text(s)
p=OUT/'REPORT.md';s=p.read_text().replace('corrected commands/readouts above','corrected commands/readouts in the acceptance section').replace('Exact command above; review’s two-test pass.','Exact Coordinator command; review’s two-test pass.').replace("Exact command above; review's two-test pass.","Exact Coordinator command; review's two-test pass.");p.write_text(s)
manifest=json.loads((OUT/'patches_b21/manifest.json').read_text())
for name,item in manifest.items():
    if not name.endswith('.diff'): continue
    assert sha(OUT/'patches_b21'/name)==item['sha256']
    assert (OUT/'patches_b21'/name).stat().st_size==item['bytes']
    assert (OUT/'patches_b21'/name).read_bytes()==(OUT/'patches'/name).read_bytes()
assert (OUT/'patches/manifest.json').read_bytes()==(OUT/'patches_b21/manifest.json').read_bytes()
for relative,pin in manifest['_application']['output_sha256'].items():
    assert sha(TREE/relative)==pin==sha(REPLAY/relative),relative
    ast.parse((TREE/relative).read_text(),filename=relative)
base_pins=dict(line.split('  ',1)[::-1] for line in (Path(manifest['_application']['input_root']).parents[1]/'out/TREE_FILES.sha256').read_text().splitlines())
# Enumerate only the named, small source tree, not fixture symlinks or shared filesystems.
files={str(p.relative_to(TREE)):sha(p) for p in TREE.rglob('*') if p.is_file()}
assert len(files)==manifest['_application']['candidate_source_files']
assert hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()==manifest['_application']['candidate_source_tree_sha256']
for name,pin in base_pins.items():
    if name not in manifest['_application']['output_sha256']: assert files[name]==pin,name
print('PATCH_AND_SOURCE_PASS: four ordered patches, 22 touched files, 927 unchanged base files; candidate matches tested bytes')
for folder in ('kit_profile','kit_timing'):
    for path in (OUT/folder).glob('*.py'): ast.parse(path.read_text(),filename=str(path))
    for path in (OUT/folder).glob('*.sh'): subprocess.run(['bash','-n',str(path)],check=True)
for relative in ('REPORT.md','NOTE_FOR_TREE_REBUILD.md','SOURCE_NOTES.md','kit_profile/README.md','kit_timing/README.md'):
    path=OUT/relative
    for target in re.findall(r'\]\(([^)]+)\)',path.read_text()):
        if '://' not in target: assert (path.parent/target.split('#')[0]).is_file(),(relative,target)
for name in ('REPORT.md','NOTE_FOR_TREE_REBUILD.md'):
    s=(OUT/name).read_text()
    assert s.startswith('VERDICT: DONE ')
    assert '## Review round 3: finding -> fix -> test' in s
    for required in ('taskset -c 0-7','tests.test_so_round3',
        'tests.test_gx_carrier.GXPTests.test_two_rank_gxp_first_batch_forward_backward',
        'tests.test_gx_carrier.GXTests.test_two_rank_fsdp_replicas_checkpoint_and_exports'):
        assert required in s,(name,required)
    assert 'complete epoch plan' not in s and '0–3' not in s
note=(OUT/'NOTE_FOR_TREE_REBUILD.md').read_text()
for required in ('--steps 10','--require-coverage','--resume-pin "$RESUME_PIN"',
                 'OFF (`off1`), OFF (`off2`), then ON (`on`)', 'first_step_micro_losses',
                 'ranks[r].performance.C1_CPU_PREFETCH', 'peak_rss_bytes'):
    assert required in note,required
checks=json.loads((OUT/'evidence/round3_checks.json').read_text())
assert len(checks)==9 and all(c['accepted'] for c in checks)
assert '\nOK\n' in (OUT/'evidence/round3_plan_cli_after.txt').read_text()
assert 'FAILED (failures=1, errors=4)' in (OUT/'evidence/round3_trainer_before.txt').read_text()
assert 'FAILED (errors=6)' in (OUT/'evidence/round3_kits_before.txt').read_text()
print('GATES_AND_DOCS_PASS: 65 dedicated passes and one skip; eight unchanged baseline failure entries; required commands/fields present')
# A local metadata walk measures usage; it follows no shared fixture symlink.
workspace_bytes=int(subprocess.check_output(['du','-sb',str(ROOT)],text=True).split()[0])
assert workspace_bytes < 3_000_000_000,workspace_bytes
print('WORKSPACE_BYTES: '+str(workspace_bytes))
stamp=subprocess.check_output(['date','-u'],text=True).strip()
paths=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name != 'ARTIFACTS.json')
paths += [ROOT/'work'/name for name in ('run_cpu_tests.py','run_round3_checks.py','test_local_parity.py',
    'test_kits.py','test_review_kits.py','test_kit_utilities.py','test_round2_kits.py','test_round3_kits.py',
    'test_round3_plan_cli.py','package_round3.py','finalize_round3.py','round2_b21_gloo_by_coordinator.txt')]
records={str(p.relative_to(OUT)) if p.is_relative_to(OUT) else '../work/'+p.name:
         dict(bytes=p.stat().st_size,sha256=sha(p)) for p in paths}
(OUT/'ARTIFACTS.json').write_text(json.dumps(dict(verified_utc=stamp,review_round=3,verdict='DONE',
    base_pin=manifest['_application']['base_pin'],candidate_source_tree_sha256=manifest['_application']['candidate_source_tree_sha256'],
    local_dedicated_cases=66,local_passes=65,local_skips=1,baseline_failure_entries=8,
    coordinator_gloo='Round-2 build 21: 23 OK; revised 31-test round-3 gate requires lane execution',
    gpu_kits='not run',workspace_bytes=workspace_bytes,artifacts=records),indent=2)+'\n')
(ROOT/'work/STATUS.md').write_text(f'''Updated {stamp}. Started 2026-11-19T12:15:19Z; deadline 2026-11-19T14:15:19Z.

VERDICT: DONE. All requested round-3 findings are fixed. out_round3 preserves the input delivery. The report and hand-over note begin VERDICT and contain the requested finding -> fix -> test section, exact continuation commands, corrected gains and current evidence scope.

Build 21 only: four ordered patches in out/patches_b21 and identical out/patches copies. All 936 input pins were checked; replay matches all 22 touched files with zero fuzz and offsets, while 927 base files remain unchanged. Candidate source has 949 files and digest {manifest['_application']['candidate_source_tree_sha256']}. Input trees and fixtures remain read-only.

Dedicated local checks: 65 passes and one skip, including five failing-before/passing-after trainer regressions, seven kit gates and a pinned-checkpoint CLI/output-filter gate. Broader suites reproduce the same eight baseline failure entries. Exact outputs are under out/evidence; out/ARTIFACTS.json records final hashes. Workspace usage is {workspace_bytes} bytes, below 3 GB.

Production changes: default-OFF synchronous budget fallback with cumulative step counter; conditional performance provenance; real-train startup regression; restored class docstring. The three-value frozen tuple stays intact when fallback is OFF. The fallback value joins existing rank agreement when enabled. The bounded audit checks first 10 continuation updates x four ranks x two arms, actual augmented pose execution, emitted grid caps, encoded hashes, row draws, RNG and process peak RSS. One-step replay runs OFF, OFF, ON from the same checkpoint and audited plan, with bitwise acceptance when OFF agrees or per-scalar OFF spread otherwise.

The supplied round-2 build-21 coordinator passed 23 tests in 1016.666 s; the review also passed those 23 and both GX cases. This changed series requires the exact 31-test lane command in REPORT, including asymmetric fallback and both GX tests. Sockets and GPUs were not used here. Real production augmentation/processor, replay, memory and performance measurements remain host checks. No speedup is claimed. No Git, SSH, deletion or external job was used.
''')
print('ROUND3_FINAL_DELIVERY_AUDIT_PASS '+stamp)
