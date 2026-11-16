"""Seal the build result after every active CPU check has completed."""
from datetime import datetime,timezone
from pathlib import Path
import sys
B=Path(__file__).resolve().parents[1];sys.path.append(str(B/'code'))
from adapter import *
package=load(B/'out/PACKAGE.json');tests=load(B/'out/TESTS.json');coverage=load(B/'out/UNEXECUTED.json')
real=load(B/'work/rh_real_final/RESULT.json');original=load(B/'out/rehearsal/RESULT.json')
assert real['passed'] and original['passed']
dump(B/'out/rehearsal/REAL_RESULT.json',real)
for name in ('REPORT.json','REPORT.md'):(B/name).write_bytes((B/'work/rh_real_final'/name).read_bytes())
raw=load(checked(real['raw']))
dump(B/'out/rehearsal/TOWER_PROGRESS.json',dict(complete=True,raw=real['raw'],captures=len(raw['captures']),outputs=list(raw['captures'].values())))
value=dict(status='BUILT_CPU_VERIFIED_NOT_LAUNCH_READY',launch_ready=False,package=package,tests=tests,
    rehearsal=dict(logic=pin(B/'out/rehearsal/LOGIC_RESULT.json'),cli=pin(B/'out/rehearsal/CLI_RESULT.json'),real_tower_with_fixture_heads=pin(B/'out/rehearsal/REAL_RESULT.json'),namespace=pin(B/'out/rehearsal/NAMESPACE.json')),
    coverage=dict(source=pin(B/'out/UNEXECUTED.json'),counts=coverage['counts'],passed=coverage['passed']),
    comparators=pin(B/'out/SCORER_CHECK.json'),proof_keys=pin(B/'out/PROOF_KEYS.json'),cpu_proof=pin(B/'out/PROOF_CPU.json'),
    decisions=pin(B/'out/DECISIONS.md'),assets=pin(B/'out/ASSET_STATUS.json'),storage=pin(B/'out/STORAGE.json'),
    blockers=load(B/'out/FAMILY.json')['blockers'],
    not_checked=['GPU checkpoint restoration, own depth/gravity prefill and token generation','GPU parity and historical run-to-run equality','Full item read and full-corpus frame staging','Production namespace: nested bwrap denied','Original Orchard launcher admission, generation-pinned cloud staging and remote returns','Unexecuted inherited tests and uncovered source lines identified in the inventories'])
dump(B/'out/FINAL_RESULT.json',value)
(B/'STATUS.md').write_text('The kit is built and CPU-verified, but is not launch-ready. `out/FINAL_RESULT.json` records the package hashes, test results, rehearsal receipts, coverage classes and unresolved checks. The real frozen tower completed on both supplied sample scenes; `out/rehearsal/REAL_RESULT.json` records the subsequent read with synthetic checkpoint heads and token generation. `out/rehearsal/CLI_RESULT.json` records the integrated command-line path. Nested bwrap was denied. Full frames, runtime and FLA are absent, and GPU parity, historical equality, production staging and remote returns remain unverified. No background build test remains active.\n')
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%MZ')
lines=['RESULT: built and CPU-verified; not launch-ready. Full evidence: out/FINAL_RESULT.json.',
 f"Code SHA256 {package['code']['sha256']}: out/c.tar (receipt out/PACKAGE.json).",
 f"Family SHA256 {package['family']['sha256']}: out/FAMILY.json (receipt out/PACKAGE.json).",
 f"Diff +{package['added']}/-{package['removed']}: out/DIFF_STATS.json; out/DIFF_vs_C8R.patch.",
 f"New tests passed: {tests['new']['run']}; inherited passed: {tests['inherited']['run']}; inherited unexecuted: {tests['inherited']['unexecuted']}. Sources: out/TESTS.json and out/LEGACY_TESTS.json.",
 f"Real CPU tower and mixed read passed: {real['captures']} captures, {real['items']} supplied items. Source: out/rehearsal/REAL_RESULT.json.",
 'The supplied scenes contain 9 items, not the requested 11; membership: work/rh_cli_complete/i/BOUND.json.',
 'Decode and checkpoint heads remain synthetic; actual scale conversion, gravity guard, dispatch, refusal injection, replay, scoring, merge and report executed. Sources: out/rehearsal/REAL_RESULT.json and out/rehearsal/CLI_RESULT.json.',
 'Nested bwrap failed with NETLINK_ROUTE permission denial: out/rehearsal/NAMESPACE.json. Operator commands: out/rehearsal/RUNBOOK.md.',
 'Comparator scores reproduced: 450 each, primaries 66.95 and 68.71. Source: out/SCORER_CHECK.json.',
 'Unexecuted line classes: '+', '.join(f'{k}={v}' for k,v in coverage['counts'].items())+'. Source: out/UNEXECUTED.json.',
 'Decisions: isolated driver; unchanged scorer copies; fixed canary/order; clustered intervals; actual sample membership; explicit synthetic boundaries; fail-closed launch status. Source: out/DECISIONS.md.',
 'Not checked: GPU restoration/parity/decode, historical GPU equality, full frame read, production dependency closure, original Orchard admission, cloud staging and remote returns. Source: out/FINAL_RESULT.json.',
 'Full frames, runtime and FLA are absent: out/ASSET_STATUS.json. No job was submitted.']
assert len(lines)<=40
existing=list((B/'events').glob('*_RESULT_final.md'))
assert len(existing)<=1
(existing[0] if existing else B/'events'/f'{stamp}_RESULT_final.md').write_text('\n'.join(lines)+'\n')
print(str(B/'out/FINAL_RESULT.json'))
