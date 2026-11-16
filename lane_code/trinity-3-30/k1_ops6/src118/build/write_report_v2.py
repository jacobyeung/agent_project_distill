"""Write the review state from checked artifacts, without inherited status prose."""
import json
import math
import dis
import types
from pathlib import Path

import job_support as H

ROOT = Path(__file__).resolve().parent

def main():
    load = lambda p: json.loads((ROOT / p).read_text())
    manifest = load('manifest_v2/DIFF.json')
    package = load('packet/PACKAGE.json')
    upload = load('packet/UPLOAD.json')
    names = load('evidence/NAMES.json')
    latest = Path(load('evidence/V2_LATEST.json')['run'])
    result = json.loads((latest / 'RESULT.json').read_text())
    coverage = json.loads((latest / 'COVERAGE.json').read_text())
    def executable(code):
        lines = {line for _,line in dis.findlinestarts(code) if line > 0}
        for value in code.co_consts:
            if isinstance(value, types.CodeType):
                lines |= executable(value)
        return lines
    for filename,row in coverage.items():
        current_sha = H.sha(filename)
        if row.get('sha256') != current_sha:
            possible = executable(compile(Path(filename).read_text(), filename, 'exec'))
            row.update(sha256=current_sha, executed=0, total=len(possible),
                       executed_lines=[], unexecuted_lines=sorted(possible))
    # Union only coverage that names the exact current source bytes. Line numbers
    # from an edited wrapper cannot certify its replacement.
    for old_path in sorted((ROOT / 'evidence').glob('v2_*/COVERAGE.json')):
        for filename,row in json.loads(old_path.read_text()).items():
            if filename not in coverage or not row.get('sha256') or row['sha256'] != coverage[filename].get('sha256'):
                continue
            target = coverage[filename]
            executed = set(target['executed_lines']) | set(row['executed_lines'])
            possible = set(target['executed_lines']) | set(target['unexecuted_lines'])
            target.update(executed=len(executed & possible), executed_lines=sorted(executed & possible),
                          unexecuted_lines=sorted(possible - executed))
    H.dump(ROOT / 'evidence/COVERAGE_V2.json', coverage)
    namespace = load('rh/local/out/RESULT.json')
    polling = load('evidence/METADATA_POLL.json')
    archive = load('rh/ARCHIVE.json') if (ROOT / 'rh/ARCHIVE.json').exists() else None
    prepared = result.get('prepared', {})
    misses = []
    compact = []
    for name,row in sorted(coverage.items()):
        display = str(Path(name).relative_to(ROOT)) if Path(name).is_relative_to(ROOT) else name
        compact.append(f"{display}: {row['executed']}/{row['total']} executable lines ({100*row['executed']/max(1,row['total']):.1f}%)")
        misses.append(display + ': ' + ','.join(map(str, row['unexecuted_lines'])))
    (ROOT / 'evidence/COVERAGE_V2.txt').write_text('\n'.join(compact) + '\n')
    shell_lines = len((ROOT / 'packet/a7e31d84.sh').read_text().splitlines())
    misses.append(f'packet/a7e31d84.sh: 1-{shell_lines}; syntax checked, allocation bootstrap not executed')
    (ROOT / 'evidence/UNEXECUTED_V2.txt').write_text('\n'.join(misses) + '\n')
    gaps = []
    if not prepared.get('passed'):
        gaps.append('The real prepared check reaches its final model-metadata lookup; the required 10,240-byte model tar is absent.')
    if not archive:
        gaps.append('RH_1_3.tar is not built: the mandatory heavy-I/O question has no answer. Its complete builder and local layout are supplied.')
    if not names['passed']:
        gaps.append('The strict external-name audit fails for existing native input names and host-side source mirrors. Internal path exemptions do not grant an external mirror exception.')
    gaps += ['The namespace has not executed on trinity-1-3; the local bwrap invocation was denied NETLINK_ROUTE creation.',
             'The full production batch, runtime bootstrap, real export/base/anchor staging and GPU prefill remain unexecuted. Component coverage is not full-job coverage.',
             'The f3069074.tar alias must have C8r archive SHA256 20a2ab6c54e22baba2c6b9065a7c0df24a9fe60a867fb078a017859dac2fdaca; its byte equivalence cannot be checked here.',
             'The orchestrator must record v2 SHA256 in amendment 2, review this package and give GO before submission.']
    status = dict(status='PREPARED_WITH_GAPS_NOT_SUBMITTABLE', submitted=False, uploaded=False,
                  manifest_v2_sha256=manifest['v2_sha256'], source_sha256=package['source'],
                  metadata_verified=polling['verified'], real_prepared_passed=prepared.get('passed',False),
                  component_rehearsal_passed=result.get('component_rehearsal_passed',False),
                  full_job_rehearsal=False, namespace_local=namespace, rh_archive_built=archive is not None,
                  strict_external_names_pass=names['passed'], blockers=gaps)
    H.dump(ROOT / 'STATUS.json', status)
    table = []
    for label, tokens in [('low',2175),('mid',8192),('full',16384)]:
        seconds = 26.336 + .046 * tokens
        capacity = math.floor((43200-1800-max(3000,seconds)-900)/seconds)
        table.append(f'{label:6} {tokens:6} {seconds:9.3f} {300*seconds/3600:9.3f} {capacity:5} {math.ceil(300/capacity):4}')
    exempt = load('packet/EXEMPT_PATHS.json')['patterns']
    selected_coverage = [line for line in compact if line.split(':')[0] in (
        'batch_entry.py','stage_job.py','phase_worker.py','job_support.py','phase_support.py')]
    text = f'''PREPARED WITH GAPS — NOT SUBMITTABLE. Nothing was submitted or uploaded.

The package contains manifest v2, a source upload, an embedded native-form batch,
staging/worker/return adapters, a portable namespace rehearsal builder, and CPU
component evidence. It does not establish a complete production-job rehearsal.
All writes stay under this workspace. No Git, SSH, network, GPU, kill or deletion
command ran. CPU work used nice 19 and one OMP/MKL/OpenBLAS thread.

OPEN REQUIREMENTS
''' + '\n'.join(f'{i}. {gap}' for i,gap in enumerate(gaps,1)) + f'''

MANIFEST V2 / AMENDMENT 2
Builder: make_manifest_v2.py. Output: manifest_v2/a40fbc19.json.
v1 byte SHA256: {manifest['v1_sha256']}
v2 byte SHA256: {manifest['v2_sha256']}
v1 BINDING digest: {manifest['v1_binding_digest']}
v2 BINDING digest: {manifest['v2_binding_digest']}
The builder asserts canonical equality after reverting only gpu.config and
gpu.data_receipt. All 300 capture values and gpu.artifact remain equal.
The exact printed diff follows; manifest_v2/DIFF.json is machine-readable.
{json.dumps(manifest['diff'],indent=2)}
The orchestrator owns the external amendment record. This build does not edit it.
Own, convert and tables use v2. The tower comparison checks sources and producer;
it records the tower's v1 manifest digest instead of falsely requiring equal
v1/v2 manifest digests. Individual capture bindings and checkpoint stay equal.

REAL PREPARATION
The local metadata tar is {polling['expected_bytes']} bytes. Its verified state is
{polling['verified']}; expected SHA256 is {polling['expected_sha256']}.
Polling records: evidence/METADATA_POLL.json. The first checks were manual;
the bounded watcher records its own two-minute observations.
The exact prepared-check result is:
{json.dumps(prepared,indent=2)}
The job calls the unchanged read_runtime.prepared and checks trainer.identity(cfg)
equals 84ea03af6049a179bf4a44619b1534fdcb528b5511544189236254b5d66842cb
and artifact.config_sha256. It does not create a preparation receipt.
The CPU mapping preserves pin paths and bytes; it redirects only exact file IO.
The reconstructed 9,881,600-byte trainer archive matches C8r's exact SHA256:
845b17895e466671bc5c5ecdb6a5a5d697a43a5e02d07d1555b11be74f8fd415.
It is payload/a845b1789.tar and accompanies the portable CPU package.
The reader also needs the pinned 10,240-byte model metadata object
8005668fc14ce5ee088d0d631d581f62ca73e6cb8130fde4a2deb73de74f635b.
Its job staging is implemented; a local model copy can be supplied as
inputs/model.tar (or A_MODEL for the CPU harness).

FIXED PHASE SEMANTICS / TOKEN OBSERVER
The pinned boundaries.GPU.own calls _prepare_decode(...).heads. That function
prefills the prompt and returns state; it does not enter _generate_one's Row.step
loop. The unchanged own phase therefore generates zero sampled tokens per capture.
The max_new_tokens=16384 argument does not make this call generate 16,384 tokens.
phase_worker.py installs a Python profile observer. On the actual _prepare_decode
return it reads prompt_length and records generated_tokens=0; it does not replace
the returned state, change a callable, retain tensors or alter any source file.
The same observer watches the completed journal call after each capture commit.
It records elapsed seconds in TOKENS.json, validates the first three own.npz
files, and publishes CANARY.json and the partial root to both pool and GCS before
returning control for capture four. A missing observation, failed canary or failed
return stops execution. The CPU fixture labels its token counts synthetic.
Source identity is checked before and after the run. evidence/kit_v2.diff is empty;
evidence/KIT_V2.json confirms all 1,018 source/input-map entries retain their bytes.

JOB, RESUME AND RETURN
packet/a7e31d84.sh embeds a small bootstrap in the native launcher form.
batch_entry.py probes the pool and prints free space before staging. It holds a
nonblocking lock on the persistent return root to serialize allocations.
It requires 200 GiB of local free space and 600 MB plus 1 MiB in the pool,
authenticates the assigned job-private /tmp mount, and attempts to return staging
errors before exiting. Cache, temp, home and output share that local mount.
stage_job.py uses native copy_parts, cloud, extract_stream, runtime_links,
extract_named, runtime_spec and namespace. It stages export, anchors, metadata,
source bundle, model metadata, base, runtime and overlays, then builds the namespace.
The source and metadata hashes are mandatory; unknown upload generations are
resolved once and the resulting immutable generation is read and byte-verified.
The phase worker checks sources, prepared identity, manifest and tower source/
producer equality. It restores a hash-verified snapshot, refuses incomplete,
HALTED or STOP roots, computes the budget and invokes k1_pipeline.main with
cache --phase own and the computed --max-seconds. The fixed logical phase root is
/scratch/jjyeung/a7e31d84/r/a/native/probe.
The budget is floor(43200 - measured setup - 3000 - 900). The 3000-second initial
capture reserve grows if a capture exceeds it. A commit observer stops before
the return margin is consumed. This is a conservative bound, not a measured GPU
maximum or a guarantee against a hang. Scheduler preemption can leave an
incomplete root; the wrapper does not delete, repair or automatically retry it.
Snapshots use the native publisher's tar, pool readback and GCS readback. Both
channels must verify before the resume pointer advances. Each allocation uses a
separate opaque pool directory to respect the native publisher's 1-GiB pool cap.
The next job restores only the phase root after authenticating the entire return;
it does not inherit a prior job's terminal marker. Output remains on node-local
storage because a project-filesystem bind can fail the phase's 100-GiB reserve.
The native pool worker runs inline, avoiding its kill-on-timeout subprocess path;
a stalled operation has no retry or automatic relaunch. The initial probe preserves
its named 4-KiB file. Logs, progress and the per-file hash manifest enter the return.
An allocation-boundary STOP is rewritten to the phase's supported RESUME value
after a clean stop; a canary STOP remains a refusal. No file is deleted.
The native EXIT status describes full-phase completion; intermediate snapshots
are not complete reads. Canary success is recorded in metadata/CANARY.json.

NATIVE DIFF AND REUSE
evidence/wrappers_v2.diff compares stage_job, batch_entry, phase_worker and
job_support with C8r native_stage, native_job, native_worker and orchard_results.
It is a wrapper replacement diff; the helpers named below retain C8r's bytes:
chain_save.py, orchard_stage.py, orchard_job.py, orchard_results.py,
native_bootstrap.py and orchard_native/native_stage.py.
evidence/NATIVE_REUSE_V2.json verifies these six files against C8r FAMILY.code_pins.
Adaptations cover the own controller, required dual-channel canary, resume pointer,
budget, source closure, return pool, inline pool worker and writable run-parent bind.
The namespace builder retains native_stage.namespace and adds only return-root,
credentials and run-parent binds. GPU runtime bootstrap remains C8r's implementation.

CPU EVIDENCE AND COVERAGE
Current run: {latest.relative_to(ROOT)}
Component rehearsal passed: {result.get('component_rehearsal_passed',False)}.
Staging controller: {result.get('staging_controller',{}).get('passed',False)}.
Resume: {json.dumps(result.get('resume',{}),sort_keys=True)}
Canary failure stops: {result.get('canary_failure_stops',False)}.
Allocation-boundary resume: {json.dumps(result.get('allocation_budget_resume',{}),sort_keys=True)}
The harness checks a separate 300-capture fixture manifest, then runs six captures.
Its changed frames do not prove that production anchors have been checked here.
Substitutions are recorded explicitly in the run's RESULT.json:
{json.dumps(result.get('substitutions',[]),indent=2)}
Line coverage per monitored file is evidence/COVERAGE_V2.txt and the run's
COVERAGE.json. Exact unexecuted line numbers are evidence/UNEXECUTED_V2.txt.
No 1-3 execution result has been received, so none of these misses is credited
to 1-3. The list includes branches, imports outside the tracing interval, uncalled
native helpers, production bootstrap and the complete allocation bootstrap.
{chr(10).join(selected_coverage)}

PORTABLE NAMESPACE REHEARSAL
Builder: build_rh.py --pack-env. Local layout: rh/local/.
Operator command after extracting under /scratch/jjyeung/orch_n30/k1_partb_rh:
  cd /scratch/jjyeung/orch_n30/k1_partb_rh && bash run_rh.sh
It binds the included p1cpu and uv-python runtime at their original logical paths,
uses local GCS/pool stand-ins, and writes out/RH_RESULT.tar even on namespace failure.
The interpreter trees total 1,495,142,412 source bytes; the writer caps the complete
archive at 3,000,000,000 bytes and throttles its one stream to 8 MiB/s.
Current archive record: {json.dumps(archive,sort_keys=True)}
The same script's local bwrap result is {json.dumps(namespace,sort_keys=True)}.
The local log says: bwrap: loopback: Failed to create NETLINK_ROUTE socket:
Operation not permitted. It was not bypassed. rh/local/out/RH_RESULT.tar contains
the pre-bwrap evidence and log. The remote namespace remains unrehearsed.

NAMES AND EXEMPTIONS
The chosen job/pool/code/log names pass: {names['new_job_pool_code_log_names_pass']}.
The complete external-name audit passes: {names['passed']}.
It reports {names['external_source_mirror_hits']} host source-mirror hits plus these
existing input hits: {json.dumps(names['existing_input_hits'],sort_keys=True)}
The actual grep input is packet/EXTERNAL_NAMES.txt; evidence/NAMES.json records
the pattern, every hit and false-positive handling. The raw batch's base64 payload
can contain accidental text matches; its decoded config and file inventory are
audited separately. SAMPLER in VLLM_USE_FLASHINFER_SAMPLER denotes sampling, not SAM.
The immutable internal namespace patterns exempted by the ruling are:
''' + '\n'.join('  ' + p for p in exempt) + f'''
packet/EXEMPT_PATHS.json contains the exact source-path list as well. The builder
does not claim that these exemptions cover host-side mirrors, external input URIs
or raw native logs. Those exposures require implementation changes before GO.

UPLOADS AND COMMANDS (NOT EXECUTED)
Source object: gs://cmu-gpucloud-jjyeung/{upload['name']}
Local file: packet/d6e92a81.tar
Bytes: {upload['bytes']}
SHA256: {upload['sha256']}
Bundle inventory: packet/FILES.json ({len(load('packet/FILES.json'))} members before its hash map).
The bundle contains the pinned kit/dependency closure, native reader modules,
all 792 sealed trainer-tree files, source guard inputs, original artifact JSON,
tower BINDING, both manifest files and C8r's two import-overlay sources.
The bootstrap also embeds the five new wrapper files and six native helper files.
Batch file: packet/a7e31d84.sh; bytes {package['batch_bytes']};
SHA256 {package['batch_sha256']}.
Submit command, after every open requirement is resolved and the orchestrator's GO:
{(ROOT / 'submit_command.txt').read_text()}
Fetch command template (substitute RETURN_TOKEN from the returned pointer/receipt):
{(ROOT / 'fetch_command.txt').read_text()}
The source upload and return fetch must use the operator's registered governor
stream. No upload command was run here. The anchor object, export parts, metadata,
model metadata and native runtime assets are existing inputs; this build does not
claim to have checked their remote availability or invent upload generations.
The external ledger is outside the write boundary. Its proposed rows remain local.
Workspace storage: {json.dumps(load('evidence/STORAGE_V2.json'),sort_keys=True)}

JOB-COUNT PLANNING
Native_r3 measured roughly 0.046 seconds per sampled token (20.6-22.5 tok/s with
light tools; 5.6 tok/s for ground-heavy work). Prompts were about 4,700 tokens;
native read items generated at most 2,175 tokens. Prompt tokens are not sampled
tokens and must not be charged at the decode rate without a separate assumption.
The table models a hypothetical full generation, not the fixed prefill-only own
call. To match the supplied 780-second full-budget case, it assumes 26.336 seconds
of fixed per-capture overhead: t(T)=26.336+0.046*T. That overhead is an assumption,
not a measured own prefill cost. Setup=1800 s, return margin=900 s, capture reserve
=max(3000,t). Capacity=floor((43200-1800-reserve-900)/t); jobs=ceil(300/capacity).
case   tokens  seconds   GPU-hours capacity jobs
{chr(10).join(table)}
The full row is 780 seconds/capture and 65 GPU-hours. Ground-heavy token rates can
exceed that range (16,384/5.6+26.336 is about 2952 s/capture). The fixed own job's
sampled-token count is zero, so its job count must use the canary's measured
prefill/head time; the token-rate table is not an empirical own-time forecast.

WRITING
The no-archaeology skill governs this report. No borderline process-history
sentence was retained. Provenance and comparison sections identify source files.
'''
    (ROOT / 'REPORT.txt').write_text(text)
    H.dump(ROOT / 'RESULT.json', dict(status=status, report='REPORT.txt', manifest_script='make_manifest_v2.py',
                                    manifest_diff='manifest_v2/DIFF.json', wrapper_diff='evidence/wrappers_v2.diff',
                                    rehearsal=str(latest.relative_to(ROOT) / 'RESULT.json'),
                                    unexecuted='evidence/UNEXECUTED_V2.txt', coverage='evidence/COVERAGE_V2.txt'))
    print(json.dumps(dict(status=status['status'], real_prepared_passed=status['real_prepared_passed'], gaps=len(gaps))))

if __name__ == '__main__':
    main()
