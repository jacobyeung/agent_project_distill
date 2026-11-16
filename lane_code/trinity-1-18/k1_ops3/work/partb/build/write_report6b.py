"""Write the reader handoff from validated build-6 evidence."""
import json
import os
from pathlib import Path
import shutil
import stat

import job_support as H

ROOT = Path(__file__).resolve().parent


def main():
    validation = json.loads((ROOT/'evidence/REPORT6B_VALIDATION.json').read_text())
    archive_validation = json.loads((ROOT/'evidence/REPORT6B_ARCHIVE_VALIDATION.json').read_text())
    rehearsal = json.loads((ROOT/'evidence/REPORT6B_REHEARSAL.json').read_text())
    component = json.loads((ROOT/'evidence/REPORT6B_COMPONENT.json').read_text())
    assert validation['passed'] and archive_validation['passed'] and rehearsal['passed']
    assert component['component_rehearsal_passed']
    package, archive = validation['batch'], archive_validation['archive']
    coverage = json.loads((ROOT/'evidence/REPORT6B_COVERAGE.json').read_text())
    coverage_summary = []
    for name in ('batch_entry.py','stage_job.py','phase_worker.py'):
        rows = [row for key,row in coverage.items() if key.split('@')[0] == name or key.startswith(name+':')]
        if not rows:
            rows = [row for row in coverage.values() if any(Path(s).name==name for s in row['sources'])]
        assert len(rows)==1, (name, len(rows))
        coverage_summary.append(f"{name} {rows[0]['executed']}/{rows[0]['total']}")
    seen, total = set(), 0
    for parent, directories, files in os.walk(ROOT, followlinks=False):
        for name in files:
            path = Path(parent)/name
            info = path.lstat()
            inode = (info.st_dev, info.st_ino)
            if stat.S_ISREG(info.st_mode) and inode not in seen:
                seen.add(inode)
                total += info.st_size
    free = shutil.disk_usage(ROOT).free
    assert total < 45_000_000_000 and free > 200*1024**3
    H.dump(ROOT/'evidence/REPORT6B_SPACE.json', dict(unique_file_bytes=total,
        cap_bytes=45_000_000_000, filesystem_free_bytes=free))
    previous = (ROOT/'evidence/build6b_saved/REPORT6.txt').read_text()
    audit = previous.split('CONFIG/a.json fields checked',1)[1].split('\n\nRehearsal implementation',1)[0]
    report = f'''part_b_short_job — READY FOR READER REVIEW. No submission ran; orchestrator GO is required.

The staging failure came from prose in anchors.members. CONFIG/a.json now contains the
real anchor tar's exact 9,601-entry inventory: 9,600 PNGs and ANCHORS_MANIFEST.json.
Native copy_parts, H.unpack(strip=0), and NS.verify_inventory pass on that production
item. Full manifest-v2 preflight checks all 300 captures against their real anchor pins.
Evidence: evidence/REPORT6_ANCHORS.json and evidence/REPORT6B_REHEARSAL.json.

The anchor generation is 1794806692483376; the code generation is 1794820770137604,
with CRC32C lDDvFQ==. Describe targets the pinned generation and rejects size,
generation or CRC32C mismatch. Configuration regressions reject prose inventories,
placeholder generations and wrong numeric types (evidence/REPORT6_REGRESSIONS.json).

The sealed a.json has allocation_seconds=10800 and no absolute deadline. Both worker
budget sites cap this duration by an optional deadline relative to started_unix.
The capture window subtracts setup, the 3,000-second capture reserve and 900-second
return margin. The --deadline-unix option passes its builder round trip. Allocation,
deadline and zero-budget tests return cleanly with code 4, RESUME, an advanced pointer
and no FAILED.json. Evidence: REPORT6_DEADLINE_CLI.json and REPORT6B_REHEARSAL.json
under evidence/; REPORT6B_COMPONENT.json also verifies an expired deadline and resume.

The embedded tar uses deterministic gzip supported by the unchanged launcher.
The kit, source_identity members, manifest v2 and six C8r helpers are unchanged.
evidence/REPORT6B_VALIDATION.json checks the sealed files and verifies
evidence/REPORT6_JOB.diff against batch fc9ed8a8's decoded payload.

Batch: packet/a7e31d84.sh
Bytes: {package['batch_bytes']}
SHA256: {package['batch_sha256']}
Source: q8/b7e31d84a90c62f5/d6e92a81.tar
Bytes: {package['source_bytes']}
SHA256: {package['source']}
The source bytes are unchanged; no source rebuild or upload is needed.

Submit command (operator only, after reader review and orchestrator GO; not run):
/usr/local/bin/sbatch --parsable --account=mt01 --partition=general --nodes=1 --ntasks=1 --gres=gpu:1 --cpus-per-task=16 --mem=200G --time=03:00:00 --no-requeue --output=/dev/null --error=/dev/null --chdir=/tmp --job-name=a15_cot_apb7e31d84a90c62f5 < a7e31d84.sh

CONFIG/a.json fields checked{audit}

All nine mapped batch cases pass: success, deadline, allocation, zero_budget,
staging_error, pool_refusal, worker_failure, publish_error and local_refusal.
The sealed production CONFIG differs only in pool/cloud/pointer transport destinations.
Stand-ins use production object names and pool paths. The success case commits six
CPU captures and verifies both canary and final returns. The separate component test
stops after three captures, resumes to six without repeating them, and preserves
committed receipts. It also verifies allocation-stop and expired-deadline resumes.

Production verifiers ran for anchors, code, metadata, model metadata and trainer tar;
native preparation checks and source/BINDING checks pass. Later batch cases reuse the
verified anchor extraction. Export/base/runtime/numpy/closure/FLA/bwrap are substituted;
their production asset verifiers did NOT run. Cloud describe replies, transport, the
interpreter, GPU decode and time-boundary inputs are simulated. The batch preflight uses
the unchanged production manifest; the CPU workload uses six captures and one real PNG.
The separate resume component uses its explicitly synthetic manifest. Per-case
CONFIG_IDENTITY.json and VERIFIERS.json record these boundaries.

Local batch: {Path(rehearsal['run']).relative_to(ROOT)}/RESULT.json
Local component: {Path(component['run']).relative_to(ROOT)}/RESULT.json
Logs: evidence/REPORT6B_BATCH.log and evidence/REPORT6B_COMPONENT.log.
Coverage union: {', '.join(coverage_summary)}.
evidence/REPORT6B_COVERAGE.txt lists unexecuted lines per file; this is CPU coverage.
Mapped mode uses Python 3.12 and does not exercise bwrap, the target node's interpreter,
live cloud authentication or GPU execution. The r5 launcher records namespace and
system-Python results separately. No full GPU-rehearsal claim is made.

Portable archive: rh/RH_1_3.tar
Bytes: {archive['bytes']} (below 5,000,000,000)
SHA256: {archive['sha256']}
The archive carries the real 2,646,947,840-byte anchor tar and both CPU environments.
evidence/REPORT6B_ARCHIVE_VALIDATION.json verifies its hash, packaged files, production
anchor hash and environment presence. No local-only anchor variant is needed.

On trinity-1-3, after the operator places the archive at the path below, run:
set -e
mkdir /scratch/jjyeung/orch_n30/k1_partb_rh/r5
nice -n 19 tar -xf /scratch/jjyeung/orch_n30/k1_partb_rh/RH_1_3.tar -C /scratch/jjyeung/orch_n30/k1_partb_rh/r5
cd /scratch/jjyeung/orch_n30/k1_partb_rh/r5
bash run_rh.sh
Use a fresh r5. Check out/RESULT.json and its namespace/system-Python results, not only
the collector's exit code. The collector returns diagnostics even when rehearsal fails.

Workspace: {total:,} unique file bytes, below the authorized 45 GB cap;
{free:,} bytes remain free on local scratch. Existing artifacts are retained; no files
were deleted. All tests and packaging ran at nice 19 with one thread. No GPU,
submission, cancellation, network, SSH or Git ran. Ledger proposals remain local.
'''
    (ROOT/'REPORT6.txt').write_text(report)
    H.dump(ROOT/'evidence/part_b_short_job.RESULT.json', dict(name='part_b_short_job',
        ready=True, ready_for='reader_review', report='REPORT6.txt', submitted=False,
        orchestrator_go_required=True, batch=package, archive=archive,
        job_diff='evidence/REPORT6_JOB.diff', validation='evidence/REPORT6B_VALIDATION.json',
        rehearsal='evidence/REPORT6B_REHEARSAL.json',
        archive_validation='evidence/REPORT6B_ARCHIVE_VALIDATION.json'))
    print(json.dumps(dict(report='REPORT6.txt', ready=True, workspace_bytes=total,
                         batch_sha256=package['batch_sha256'], archive=archive)))


if __name__ == '__main__':
    main()
