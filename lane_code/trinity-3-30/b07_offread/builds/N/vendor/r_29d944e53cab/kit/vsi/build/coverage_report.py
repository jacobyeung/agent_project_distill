"""Report only observed local coverage and fixture evidence."""
from pathlib import Path
import gzip
import hashlib
import json
import re
import sys
K=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(K/'proof'))
import lines_report
value=json.loads((K/'proof/COVERAGE.json').read_text());records=[];job=[]
for name,row in value['files'].items():
    p=Path(name).resolve()
    if not p.is_relative_to(K) or not p.is_file() or not row['executed_lines']:continue
    rel=str(p.relative_to(K))
    records.append(dict(file=rel,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),lines=row['executed_lines']))
    if rel.startswith(('launcher/','reader/','cohort/','parity/')):job.append((rel,row))
result=json.loads((K/'proof/PASS3_LOCAL_RELEASE/RESULT.json').read_text())
for path in (Path(result['job_root'])/'t').glob('*.json.gz'):
    records.extend(json.loads(gzip.decompress(path.read_bytes()))['files'])
local=dict(schema=1,source='Observed coverage.py tests and local proof, plus stdlib Phase B subprocess trace',files=records)
(K/'proof/LOCAL_LINES.json.gz').write_bytes(gzip.compress(json.dumps(local,sort_keys=True).encode(),mtime=0))
num=sum(r['summary']['covered_lines'] for _,r in job);den=sum(r['summary']['num_statements'] for _,r in job)
summary=dict(imported_modules=len(job),covered_lines=num,executable_lines=den,line_percent=round(100*num/den,2))
(K/'proof/COVERAGE_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
passed=re.search(r'(\d+) passed in ([0-9.]+)s',(K/'tests/FINAL_TESTS.log').read_text());assert passed
source=next((Path(result['job_root'])/'sj').glob('*/r'));b=json.loads((source/'b0/PHASE_B.json').read_text())
proof=f'''# Local proof evidence

{passed[1]} tests passed in {passed[2]} seconds. The separate local proof passed with 14 official items in Phase A and 20 accepted dev-main IDs in Phase B. Its compressed archive is {result['archive_bytes']:,} bytes. No Orchard job, real GPU/model, real GCS upload or real k6tk pull ran during this build.

The local proof executes the batch bootstrap, job runner, pool write-test subprocess, authenticated fixture staging, bind, real PyAV decoding of generated MP4s, worker, budgets, merges, scorer and pool publication. A fresh Phase B subprocess runs the unchanged direct/r3/r5 path, public frame builder, accepted puller against a miniature fixture store, worker, budgets, merges and comparisons. Both local engines, processors and models are fixtures. Namespace, real processor parity and staging sources also use local substitutes. The local GCS return is explicitly unavailable; unit tests mock its command boundary and verify generations and readback hashes.

The Orchard proof keeps real H100 checks in both phases. Phase A stages the real runtimes/base/export and all 288 videos, decodes the full plan, compares first-20 dev prompts using the real processor, and executes 14 official items with only the engine boundary substituted. Phase B starts only after every Phase A gate passes, in a fresh interpreter with real vLLM. Production runs the single 4,008-item official read. Tests compare embedded files: only CONFIG mode and phase_b differ for a shared token and pool.

Phase A covers all eight subtypes with two per non-direction task plus two easy, one medium and one hard direction item. Its local proof confirms a capped source, an unparsed answer, one zero-scored B2048 continuation error and one B4096 continuation cap. The explicit 14-item total cannot accommodate two per subtype.

All 20 dev receipt reconstructions match accepted frames/0.json SHA256 pins and identify 576 PNGs. The unchanged direct binder checks the full accepted payload and prompt pins. Only smoke_items=20 changes the reader settings, after exact worker-order verification. The public frame builder realizes only selected captures. Phase B's local internal parity passes all 16 ID and two pixel checks. This validates fixture plumbing, not real processor parity.

PHASE_B.json reports prompt-byte, ON16k token/raw-text and budget-answer/score equality per item and arm, plus paired mean scores. The accepted packet lacks prompt-ID arrays but records hashes for 16 probe items; the comparison includes those hashes. Fixture comparisons are synthetic and are not evidence of accepted-model agreement. Real generation differences are reported; prompt/parity failures stop the proof.

The return path tests include a real local 4 MiB fsync/SHA256 probe and pool copy, timeout behavior without waiting for an NFS-blocked child, the 100 MB pool cap, per-mode packet caps, either-channel success, upload readback corruption, pool-to-GCS fetch fallback, the >=20 MB registration stop and Phase A failure gating. Only the explicitly authorized .wtest is removed. No cleanup of existing returns runs.

Observed coverage.py evidence covers {num}/{den} statements ({100*num/den:.2f}%) in {len(job)} imported job/parity modules. LOCAL_LINES.json.gz also includes the stdlib Phase B child trace; LINES.md reports that hash-matched union. Third-party native/vLLM/CUDA code is outside the source audit. Missing CPU paths remain gaps; no every-line claim is made.

The packet contains a pre-publication trace snapshot. A bounded pool/GCS sidecar attempt carries final publisher lines. FETCH.json records whether the final sidecar or snapshot was obtained. Sidecar failure leaves a coverage gap without invalidating the packet. All Orchard trace coverage remains pending.

Pending operator evidence: Slurm/H100/bwrap compatibility, real credentials and return paths, all four export parts, all 288 real videos, real processor parity, k6tk frame availability, real vLLM generation and accepted comparisons, final returned trace union, and two-hour feasibility. PROOF_JOB.md contains exact preparation, submission, polling, fetch and line-audit commands.
'''
(K/'proof/PROOF.md').write_text(proof)
report=lines_report.report(local)
(K/'proof/LINES_LOCAL.json').write_text(json.dumps(report,indent=2)+'\n')
text=['# Production-path line audit','',
'Local evidence is observed; Orchard is pending. This report credits no Orchard lines. Run `python proof/lines_report.py TRACE.json.gz --json LINES.json` after fetch. `--strict` fails for gaps or unmatched source hashes.','',
'The scope conservatively includes active job modules, defensive branches, unchanged dev adapters, Phase B and the accepted puller. It excludes only explicitly listed functions/modules. Only H100 checks and hardware/version gates receive the GPU-only classification; other missing lines remain gaps. Third-party engines/native code are outside this audit. A fake-engine execution does not establish GPU correctness.','',
'Coverage transfers only across equal source SHA256. Local child-process lines come from the stdlib trace. Runtime_2 or bound copies with unknown hashes remain unmatched gaps. Bytecode line counts and coverage.py statement counts use different denominators.','',
'## Scope exclusions','']
for name,funcs in sorted(lines_report.EXCLUDE.items()):text.append('- '+name+': '+', '.join(sorted(funcs)))
text+=['- Import only: '+', '.join(sorted(lines_report.IMPORT_ONLY)),'- Unused: '+', '.join(sorted(lines_report.UNUSED)),'','## Missing local lines','']
for row in report['modules']:
    text += ['### '+row['file'],'',f"Local union: {row['union']}/{row['relevant']} lines. SHA256 `{row['sha256']}`.",'']
    for group in row['functions']:text.append(f"- {group['classification']} `{group['function']}`: {lines_report.ranges(group['lines'])}")
    if not row['functions']:text.append('No missing lines in this declared scope.')
    text.append('')
text += [f"Remaining: {report['missing']} lines, including {report['gaps']} gaps. Orchard coverage is not assumed."]
(K/'proof/LINES.md').write_text('\n'.join(text)+'\n')
print(json.dumps(dict(tests=int(passed[1]),coverage=summary,archive_bytes=result['archive_bytes'],phase_b_parity=b['parity'],missing=report['missing'],gaps=report['gaps'])))
