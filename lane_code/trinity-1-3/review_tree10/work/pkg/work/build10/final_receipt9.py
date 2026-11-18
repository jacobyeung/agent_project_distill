"""Record qualification limits without promoting missing evidence to a pass."""
import hashlib,json
from pathlib import Path
B=Path(__file__).resolve().parent;L=B.parents[1]
def read(name):return json.loads((B/name).read_text())
comparison=read('SUITE_COMPARISON.json');coverage=read('CHANGED_COVERAGE.json')
packet=read('proofs/packet/results.json')
extra=[r for r in comparison['failures'] if not r['preexisting'] and 'BF16' not in r['cause']]
blockers=[
    'Full bound VQA census and production build_stream proof were not run; heavy-IO approval is unavailable.',
    'Requested original acceptance counts are not established; the units baseline differs and final admission includes the extent gate.',
    'Full R1 allocation lacks other post-filter populations and native sampler indices.',
    'Production model/frame-host and independent inference acceptance remain unqualified; carried launch blockers remain.']
gaps=coverage['classes'].get('CPU-reachable unresolved',0)
if gaps:blockers.append('CPU-reachable changed statements remain unobserved; see GAPS.json.')
if extra:blockers.append('Regressions beyond the allowed BF16 parity exception remain; see SUITE_COMPARISON.json.')
if comparison['r2_failures']:blockers.append('R2 failure events remain; see SUITE_COMPARISON.json.')
files=['DELIVERY.json','FINAL_BINDING_AUDIT.json','KIT_RESULT.json','MIX_BINDINGS.json','SUITE_COMPARISON.json',
       'CHANGED_COVERAGE.json','proofs/package/ARCHIVE.json','proofs/packet/results.json',
       'proofs/forward/RESULT.json','proofs/mutation_M02/RESULT.json','proofs/mix_accounting/RESULT.json',
       'proofs/fixture_requalification/RESUME_RECEIPT.json','proofs/suite_tree/legacy_changed/results.json']
value=dict(status='BLOCKED',GO=False,source_seal=read('DELIVERY.json')['tree_seal'],
    packet=dict(tests=len(packet),passed=sum(v['outcome']=='passed' for v in packet.values())),
    frozen_suite_complete=all(read('proofs/suite_'+v+'/results.json')['complete'] for v in ('tree','base')),
    regressions_beyond_BF16=len(extra),r2_failures=comparison['r2_failures'],cpu_gaps=gaps,
    coverage_classes=coverage['classes'],blockers=blockers,
    evidence={name:hashlib.sha256((B/name).read_bytes()).hexdigest() for name in files})
(B/'FINAL_PASS.json').write_text(json.dumps(value,indent=2)+'\n')
(B/'STATUS.md').write_text('# Build 9fix status\n\nThe source, GO=false kits, archive, packet suite, frozen-package suite, comparison and coverage records are complete. Qualification is BLOCKED. See FINAL_PASS.json and ../../out/BUILD9FIX_REPORT.md.\n\n'+''.join('- '+reason+'\n' for reason in blockers))
print(json.dumps(value,indent=2))
