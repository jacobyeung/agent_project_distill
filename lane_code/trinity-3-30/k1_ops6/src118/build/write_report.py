"""Assemble the local review handoff without submitting or accessing services."""
import ast
import difflib
import hashlib
import json
import math
from pathlib import Path
import secrets

from build_sources import ROOT


def main():
    evidence = ROOT / 'evidence'
    run = Path(json.loads((evidence / 'LATEST.json').read_text())['run'])
    result = json.loads((run / 'RESULT.json').read_text())
    package = json.loads((ROOT / 'payload/PACKAGE.json').read_text())
    pins = json.loads((ROOT / 'payload/ABSOLUTE_SHA256.json').read_text())
    coverage = json.loads((run / 'COVERAGE.json').read_text())
    native = ROOT / 'reference/sj/orch_cd/evalx/work/milestone'
    family = json.loads((ROOT / 'reference/FAMILY.json').read_text())
    used = ['chain_save.py', 'orchard_stage.py', 'orchard_results.py', 'orchard_job.py',
            'native_bootstrap.py', 'orchard_native/native_stage.py']
    reuse = {}
    for name in used:
        digest = hashlib.sha256((native / name).read_bytes()).hexdigest()
        assert digest == family['bootstrap_pins'][name]
        reuse[name] = dict(sha256=digest, bytes_unchanged=True)
    (evidence / 'native_reuse.json').write_text(json.dumps(reuse, indent=2) + '\n')
    old = (native / 'orchard_native/native_stage.py').read_text()
    node = next(n for n in ast.parse(old).body if isinstance(n, ast.FunctionDef) and n.name == 'namespace')
    old_function = '\n'.join(old.splitlines()[node.lineno - 1:node.end_lineno]) + '\n'
    new = (ROOT / 'namespace_adapter.py').read_text()
    node = next(n for n in ast.parse(new).body if isinstance(n, ast.FunctionDef) and n.name == 'namespace')
    new_function = '\n'.join(new.splitlines()[node.lineno - 1:node.end_lineno]) + '\n'
    patch = ''.join(difflib.unified_diff(old_function.splitlines(True), new_function.splitlines(True),
                                       fromfile='C8r/native_stage.py:namespace',
                                       tofile='namespace_adapter.py:namespace'))
    (evidence / 'native_wrapper.diff').write_text(patch)
    coverage_text = ['Line coverage uses CPython executable line tables and sys.settrace.',
                     'This is component coverage, not complete production-job coverage.',
                     'The report names every unexecuted line in the monitored files.',
                     'GPU decode, preparation, production bootstrap, and remote transports remain unproved.', '']
    for filename, value in coverage.items():
        coverage_text += [filename,
                          f"  Executed {value['executed']}/{value['total']} executable lines.",
                          '  Unexecuted: ' + ', '.join(map(str, value['unexecuted_lines']))]
    (evidence / 'COVERAGE.txt').write_text('\n'.join(coverage_text) + '\n')
    rows = []
    for label, tokens in [('low', 2048), ('mid', 8192), ('high', 16384)]:
        seconds = 14.6 * tokens / 2048
        available = 43200 - 1800 - seconds - 600
        capacity = math.floor(available / seconds)
        rows.append(dict(case=label, tokens=tokens, seconds_per_capture=seconds,
                         total_decode_hours=300 * seconds / 3600,
                         captures_per_job=capacity, jobs=math.ceil(300 / capacity)))
    (evidence / 'ESTIMATES.json').write_text(json.dumps(dict(
        formula='t=14.6*(tokens/2048); capacity=floor((43200-setup-t-margin)/t); jobs=ceil(300/capacity)',
        assumed_setup_seconds=1800, assumed_margin_seconds=600,
        measured_setup=False, measured_own_throughput=False, cases=rows,
        caveat='HF restore, CPU/GPU transfers and head query differ from the native reader; token scaling is not a runtime bound.'
    ), indent=2) + '\n')
    token = 'a' + secrets.token_hex(5)
    job = 'a15_cot_ap' + secrets.token_hex(5)
    script = secrets.token_hex(5) + '.sh'
    pool = '/project/community/jjyeung/okh7/' + token
    ledger = dict(status='PROPOSED_NOT_UPLOADED_NOT_SUBMITTED', job_name=job,
                  tokens={token: 'persistent result pool and cloud return prefix',
                          script: 'future reviewed batch entrypoint',
                          'd64c8e20.tar': 'source and input identity bundle'},
                  pool=pool, cloud='gs://cmu-gpucloud-jjyeung/q8/' + token,
                  destination='/scratch/jjyeung/orch_n30/k1_ops3/work/ORCHARD_LEDGER.jsonl',
                  pending_reason='Destination is outside the workspace; no external append was made.')
    with (ROOT / 'ORCHARD_LEDGER.pending.jsonl').open('a') as stream:
        stream.write(json.dumps(ledger, sort_keys=True) + '\n')
    submit = ('/usr/local/bin/sbatch --parsable --account=mt01 --partition=general '
              '--nodes=1 --ntasks=1 --gres=gpu:1 --cpus-per-task=16 --mem=200G '
              '--time=12:00:00 --job-name=' + job + ' --output=' + pool + '/%j.log ' + pool + '/' + script)
    (ROOT / 'submit_command.txt').write_text(
        'BLOCKED TEMPLATE ONLY. The batch entrypoint does not exist. Do not submit.\n'
        'The allocation flags follow C8r native_launcher.submit_argv; availability was not queried.\n' + submit + '\n')
    fetch = ('gcloud storage cat "gs://cmu-gpucloud-jjyeung/q8/' + token +
             '/${RETURN_TOKEN}/result.tar.gz#${RETURN_GENERATION}" | pv -q -L 8m > "' +
             str(ROOT) + '/${RETURN_TOKEN}.tar.gz"')
    (ROOT / 'fetch_command.txt').write_text(
        'OPERATOR TEMPLATE ONLY; no return object exists. Register the governor stream first.\n'
        'Run with pipefail and the operator\'s GCS credentials. Fill the verified return token and generation.\n'
        'No service access was performed by this build.\n' + fetch + '\n'
        'Authenticate the downloaded archive against the returned archive SHA256 and SHA256.json before convert.\n')
    filelist = '\n'.join(f"{v['sha256']}  {v['bytes']:>9}  {p}" for p, v in sorted(pins.items())) + '\n'
    (ROOT / 'FILE_LIST.txt').write_text(filelist)
    blockers = dict(status='BLOCKED_NOT_SUBMITTABLE', immutable_manifest_sha256='91a2dbf9a0bdad1a45af44a5a3a2607d40f9f7a630f742fc4531544c00cade7c',
        blockers=[
            'gpu.data_receipt.sha256 is REQUIRED, not a SHA256 digest; no file can pass the unchanged guard.',
            'gpu.config.path is a placeholder; gpu.config.sha256 is the derived trainer identity. C8r config byte SHA256 is 78341acb36ffd03b9cec6de65effc9fafcbe8bccdc1dfb43e9da7bd88af47560.',
            'C8r stages mirrored preparation metadata. The supplied code does not generate a fresh training preparation or data receipt for this job.',
            'Required immutable source paths conflict with the literal Orchard-visible naming rule.',
            'The requested ledger lies outside the writable workspace.',
            'The namespace probe was denied NETLINK_ROUTE socket creation by the execution environment.'
        ], user_decision_received=False,
        missing_deliverables=result['unexecuted_requirements'])
    (ROOT / 'STATUS.json').write_text(json.dumps(blockers, indent=2) + '\n')
    report = f'''BLOCKED — source bundle and CPU component evidence only; no deployable job packet.

Nothing was submitted, uploaded, fetched remotely, killed, or deleted. No Git, SSH,
Orchard, GCS, internet, or GPU workload ran. All persistent writes are under this build.
CPU commands used nice -n 19, empty CUDA_VISIBLE_DEVICES, and one OMP/MKL/OpenBLAS thread.
The host is trinity-1-18. The source rules were read first. No heavy archive, image,
weight, or training-data transfer ran. No external ledger append was made.

BLOCKERS
1. Manifest 91a2dbf9 contains gpu.data_receipt.sha256="REQUIRED" at line 225731.
   bindings.checked compares a computed 64-character SHA256 with that literal.
   No receipt can satisfy it. gpu.config.path is also REQUIRED_LOCAL_STEP_544_CONFIG.
2. The config pin 84ea03af... is the artifact's trainer.identity(cfg), not the
   C8r prepared config byte hash 78341acb.... carrier_c1_run.identity excludes
   preparation/admission/authorization fields (lines 38-46). check_manifest
   calls B.checked, which checks file bytes (k1_pipeline.py:39).
3. C8r native_stage stages existing small metadata objects and native_worker
   reads pinned config/data receipts. read_runtime.prepared:19-70 authenticates
   mirrored metadata. It is not a fresh preparation writer. The actual trainer
   preparation writer is carrier_c1_run.prepare:441-631; it authenticates the
   four production training streams before writing preparation_output/receipt.json.
   The supplied inputs do not establish a fresh-preparation path that preserves
   the pinned derived config identity. No fake PREPARED receipt was generated.
4. The literal naming rule forbids required paths such as /scratch/.../k1_frames
   and the fixed phase output filename own.npz.
   The C8r rule exempts immutable inputs/internal source paths, but this request
   does not. That exception requires a user ruling.
5. The ledger destination is outside the writable workspace. Its proposed row
   is ORCHARD_LEDGER.pending.jsonl, not an append to the external ledger.
6. The namespace probe failed with "bwrap: loopback: Failed to create
   NETLINK_ROUTE socket: Operation not permitted". It was not retried.

The pending question asks whether the wrapper may validate an in-memory GPU
settings copy with generated pins while phase execution retains the original
manifest and phase identity. No such override was implemented or executed.
Changing the shared manifest would instead change its digest and requires a
coordinated decision for tower/own/convert. This build changes neither identity.

SOURCE PACKAGE
Archive: payload/{package['archive']}
SHA256: {package['sha256']}
Bytes: {package['bytes']}; files: {package['files']}; source bytes: {package['source_bytes']}.
File list: FILE_LIST.txt. Machine-readable map: payload/ABSOLUTE_SHA256.json.
Builder: build_sources.py. It selects explicit dependency pins, authenticated
runtime-tree members, native modules, recorded preflight inputs, eligibility
authorities, artifact metadata, the unchanged manifest and tower BINDING.
It does not include anchors, weights, a production environment, generated
preparation metadata, or a completed launcher. Files checked by source guards
remain in the bundle even when their Python bodies are not executed.
This is an authenticated source/input closure, not a proved GPU import closure.
The builder refuses an individual file above 20 MB or a source total above 100 MB.

IDENTITIES AND DIFFS
verify_sources: 109 files pass.
DEPENDENCIES.json: aa0a728148bbf076fe1d42a6fe4bb053c761052ec653faa02f7a06e240b8ca42.
Manifest byte SHA256: 91a2dbf9a0bdad1a45af44a5a3a2607d40f9f7a630f742fc4531544c00cade7c.
Manifest semantic digest used by BINDING:
aa2fefb545d25762a4cfffb0a34bd053bfbbfbb8b064ca5256cab8d0d7506eda.
The semantic digest, source map and producer hash equal tower_sam's BINDING.
Producer: 80d763d4149f1b7989d806f3bfab0660e631c27e79d0300cd8300fbdb88f075d.
evidence/kit.diff is empty; evidence/kit_comparison.json records copied kit files.
No kit file changed. evidence/identity.json contains the exact comparison.

NATIVE REUSE
The supplied code_c8r.tar was verified as
f4535bc015da4a6e7f0d99e6db17a39fd49aa8d78dcf0a47d0aa5241b507f134 and extracted
under reference/. No extracted wrapper file changed. The component tests use
unchanged orchard_stage.copy_parts/extract_stream/unpack, native_stage.physical,
orchard_results.publish/pool_worker and chain_save's bounded archive helpers.
Their imported dependencies orchard_job.py and native_bootstrap.py are unchanged.
evidence/native_reuse.json records all six wrapper hashes against C8r FAMILY.
namespace_adapter.py adapts only native_stage.namespace for a CPU probe: it
binds the staged source tree, local interpreter and build output, hides GPU
devices and adds network isolation. It does not mount or write Orchard /home.
evidence/native_wrapper.diff compares those exact namespace functions.
phase_support.py is new wrapper support, not a modification of phase code.
No production staging/runtime/return adaptation is claimed complete.

CPU EVIDENCE
{run.relative_to(ROOT)}/RESULT.json and COVERAGE.json; evidence/COVERAGE.txt.
Native local-object copy, archive extraction, path mapping and checksum checks pass.
check_manifest('own') passes for a separate 300-capture fixture with tiny frame
and receipt pins. This does not validate production frames or preparation.
The unchanged phase runs on six fixture captures. A deterministic fixture
monotonic clock makes run 1 return 4 after three commits. Run 2 uses the same
root, preserves all three receipt hashes, skips their decode calls and finishes.
Six total boundary calls prove committed captures were not decoded again.
The canary checks three arrays and journal durations. Its failure path writes
STOP, and the fixed phase then returns 4. All these outputs are synthetic.
The unchanged native publisher archives the phase root, its file SHA manifest,
PROGRESS.jsonl and a fixture log. Both local pool and local GCS stand-ins verify.
The cloud transport and pool deadline subprocess are replaced only in this test;
the unchanged pool worker runs inline. No timeout/remote-transport proof is claimed.
The real manifest pin guard rejects the impossible data receipt, as expected.
The copied-source namespace did not execute because the environment denied bwrap.
Coverage lists executable-line misses for every monitored file; no 100% claim.
It does not cover every imported trainer module or a complete production job.

STORAGE AND RESUME DESIGN (NOT A COMPLETED WRAPPER)
Use a node-local output mapped at one fixed /scratch path. Save verified snapshots
to the project pool and restore the selected committed snapshot at the same logical
path next job. A project-FS bind would inherit the nearly full project's free-space
measurement and can fail the phase's 100 GiB + 1,500,000,000-byte floor.
Keep caches outside the phase root. Native staging also requires its 200 GiB floor.
Measure local stage/cache/temp/output and the project pool before writes. The pool
needs the next snapshot, metadata/log allowance and write-probe capacity; its
free-space requirement need not be 100 GiB because decode runs on node-local disk.
An atomic snapshot pointer must advance only after the full archive and per-file
hashes verify. A partial capture or HALTED root must be returned and refused;
no automatic deletion, quarantine, retry or receipt fabrication is permitted.
The expected root is roughly 300 x 0.7 MB = 210 MB. Retain both current and next
snapshots until the next one is verified. No disk cleanup is automated.
The first-step pool write test, snapshot restore/commit and production job log
capture remain to be implemented and rehearsed after the binding decision.

TIME BUDGET AND JOB COUNT
Use max_seconds = floor(43200 - elapsed_since_allocation_start - longest_capture
                       - return_and_safety_margin).
Log every term. elapsed must include staging, import, preparation and canary time.
phase_support.budget implements and exercises the arithmetic, but this is not
integrated with a production controller. The first canary needs a conservative
initial reserve; subsequent scheduling must account for measured capture times.
A measured maximum is not a guarantee against a longer future capture or stall.
Unexpected interruption leaves an incomplete root and requires operator review.

At t = 14.6 * token_budget / 2048 seconds/capture:
case  tokens  t(s)   decode hours  captures/job  12 h jobs
''' + '\n'.join(f"{r['case']:4}  {r['tokens']:6}  {r['seconds_per_capture']:5.1f}  {r['total_decode_hours']:12.3f}  {r['captures_per_job']:12}  {r['jobs']:9}" for r in rows) + '''
These counts assume 30 minutes of setup, a 10-minute return/safety margin and
one longest-capture reserve. Formula: capacity=floor((43200-setup-t-margin)/t),
jobs=ceil(300/capacity). These are planning cases, not measured own throughput.
The reference 636 items / 9300 seconds is 14.62 seconds/item. Own uses HF decode
plus model movement and head query; extrapolating token count alone may understate
runtime. At twice the high-case per-capture time (233.6 s), the same formula needs
two jobs. At 116.8 s, setup above 7443.2 s prevents all 300 fitting in one job.

OPERATOR FILES
submit_command.txt and fetch_command.txt contain unexecuted templates only.
The batch entrypoint does not exist; the package must not be submitted.
STATUS.json lists blockers and unfinished requirements. The independent review
must not interpret component checks as the requested full-job rehearsal.
INPUTS_PLAN.json records the four ordered export parts and the anchor archive.
It leaves the unknown anchor generation and f3069074.tar archive hash unfilled.
The local build occupies about 77 MB, below the 20 GB cap (evidence/STORAGE.json).

WRITING
The no-archaeology skill governs this report. No borderline historical-process
sentence was retained; the diff/reuse section identifies source provenance.
'''
    (ROOT / 'REPORT.txt').write_text(report)
    print(json.dumps(dict(report=str(ROOT / 'REPORT.txt'), status='BLOCKED_NOT_SUBMITTABLE',
                         source_package=package, job_name=job), indent=2))


if __name__ == '__main__':
    main()
