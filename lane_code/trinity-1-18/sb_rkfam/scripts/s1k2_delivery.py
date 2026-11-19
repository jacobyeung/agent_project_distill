"""Write an explicit blocked delivery; never manufacture selection provenance."""
from common import *

FAMILIES = [('legacy_percentile_vote', 16), ('floor_band_occupancy_closing', 24),
            ('floor_convex_hull', 18), ('plane_fit_floor_polygon', 18)]


def main():
    audit_path = W/'out/S1K2_GT_AUDIT.json'
    audit = read(audit_path)
    assert audit['status'] == 'BLOCKED' and audit['eligible_captures'] == 0
    inputs = {str(p): sha(p) for p in [audit_path, W/'out/S1K2_RULE.md', W/'BLOCKER.md',
                                     Path(__file__), W/'scripts/common.py', W/'scripts/cpu.sh']}
    provenance = W/'configs/KERNEL_PROVENANCE_S1K2.json'
    if not provenance.exists():
        write(provenance, dict(status='MISSING', origin='MISSING: family selection blocked by independent GT labels',
              intended_origin='selected on K1 training captures among 4 families, 2026-11-19',
              authorized_by='pending orchestrator', selection_scope='K1 train only',
              family='MISSING', constants='MISSING', kernel_sha256='MISSING',
              relation_to_benchmark_rule='Legacy family is registered as one candidate; no family has been scored with independent labels.',
              rebind='NOT_PERFORMED'), inputs)
    if not (W/'out/S1K2_TESTS.json').exists():
        return
    tests = read(W/'out/S1K2_TESTS.json')
    dry = read(W/'out/S1K2_DRYRUN.json')
    inputs.update({str(p): sha(p) for p in [provenance, W/'out/S1K2_TESTS.json', W/'out/S1K2_DRYRUN.json']})
    result_path = W/'out/S1K2_RESULTS.json'
    write(result_path, dict(status='BLOCKED', command='bash scripts/cpu.sh scripts/s1k2_delivery.py',
          audit_command=audit['command'], validation_command=tests['command'],
          eligible_captures=0, excluded_captures=len(audit['excluded']), rooms=audit['rooms'],
          families=[dict(family=f, grid_points=n, cross_fit_score='MISSING', interval95='MISSING') for f,n in FAMILIES],
          winner='MISSING', legacy_verdict='UNDETERMINED: no independent GT labels',
          folds='NOT_ASSIGNED: no eligible rooms', bootstrap_draws_executed=0,
          scores_computed=0, rebind='NOT_PERFORMED',
          exclusions=audit['excluded'], tests=tests['verdict'], synthetic_tests=tests['tests'],
          cpu_gate_dry_run=dry['verdict'], full_cpu_dry_run='MISSING: selected kernel unavailable',
          old_provenance_unchanged=tests['old_provenance_unchanged'],
          missing_input='Independent scan-GT room-area annotation or segmented floor mesh with authenticated capture/room mapping'), inputs)
    inputs[str(result_path)] = sha(result_path)
    (W/'OPERATOR.md').write_text('''# Room kit S1k2

Run from /scratch/jjyeung/orch_n30/sb_rkfam. This copy is BLOCKED and authorizes no inference.

The registered K1 training inputs provide no independent room-area annotation or segmented floor mesh. All 110 captures are excluded. BLOCKER.md names the missing source and the paths checked; out/S1K2_GT_AUDIT.json lists every exclusion and input hash.

out/S1K2_RULE.md preregisters four footprint families, constant grids, room folds, metric and tie-break. No family score, bootstrap interval, winner or deployment constants exist. configs/KERNEL_PROVENANCE_S1K2.json has status MISSING and authorized_by pending orchestrator; it is not an approval-ready selection record. Do not approve the inherited kernel as an S1k2 result.

The original KERNEL_PROVENANCE.json and KERNEL_FROZEN.json remain unchanged. The kit has not been rebound. Old selection, test and dry-run receipts describe only the inherited kit; they do not validate S1k2. Supply authenticated GT room areas or floor meshes on local disk before running selection, rebinding and full validation.

Reproduce this blocked delivery with these commands, sequentially:

```bash
bash scripts/cpu.sh scripts/s1k2_audit.py > out/S1K2_AUDIT.log 2>&1
bash scripts/cpu.sh scripts/s1k2_delivery.py
bash scripts/cpu.sh scripts/s1k2_validate.py > out/S1K2_VALIDATE.log 2>&1
bash scripts/cpu.sh scripts/s1k2_delivery.py
bash scripts/cpu.sh scripts/s1k2_package.py > tmp/S1K2_PACKAGE.log 2>&1
```

The validation runs selected existing synthetic tests and checks that missing provenance blocks launch. The full original suite and dry run require prohibited evaluation inputs and are not run. No new-kernel inference validation is possible without a selected kernel.

All stages use CPU only, nice priority 10 and at most eight threads. No network, SSH, Git, GPU, process termination or external writes are permitted. Keep K1 held-out, R0-dev, dev-S1 and official items closed. The archive is out/sb_rkfam.tar; its checksum is out/sb_rkfam.tar.sha256. The S1k2 packager excludes inherited archives and prohibited evaluation payloads.
''')
    (W/'KIT_SPEC_room_pricing.md').write_text('''# Room kit S1k2 specification

S1k2 is blocked by missing independent GT room-area labels. The operative family-selection protocol is out/S1K2_RULE.md. The evidence and excluded capture list are out/S1K2_GT_AUDIT.json; BLOCKER.md describes the required source and where it must be bound.

Select every footprint family and constant using K1 training captures only. Never substitute legacy rule outputs for independent room areas. K1 held-out, R0-dev, dev-S1 and official items select no rule or constant and remain unopened.

No family has been selected, no new kernel has been bound, and no inference is authorized. configs/KERNEL_PROVENANCE_S1K2.json records MISSING rather than claiming a completed origin. The original provenance and frozen constants remain unchanged. OPERATOR.md gives the commands for this blocked delivery.
''')
    gpu_inputs = {**inputs, str(W/'OPERATOR.md'): sha(W/'OPERATOR.md')}
    write(W/'out/GPU_NEED.json', dict(status='BLOCKED: independent GT room-area labels MISSING',
          measured_gpu_hours_this_task=0, gpu_requested=False, kernel='MISSING',
          authorized_by='pending orchestrator', rebind='NOT_PERFORMED',
          missing=['Independent scan-GT room-area source', 'Completed S1k2 family/constant selection',
                   'Validated kernel rebind', 'Orchestrator approval'],
          command='bash scripts/cpu.sh scripts/s1k2_delivery.py'), gpu_inputs)
    report = f'''# S1k2 family selection: BLOCKED

| Family | Grid points | Cross-fit MRA | 95% room-bootstrap interval |
|---|---:|---:|---|
| Legacy percentile cut + votes | 16 | MISSING | MISSING |
| Floor-band occupancy + closing | 24 | MISSING | MISSING |
| Floor-point convex hull | 18 | MISSING | MISSING |
| Plane-fit floor polygon | 18 | MISSING | MISSING |

Winner: MISSING. Legacy verdict: undetermined; no independent labels support a comparison.

The rule was written before scoring in out/S1K2_RULE.md. All 110 registered training captures (102 rooms) lack a qualifying independent room-area source in the audited kit inputs. All 110 GT NPZ hashes match; they contain depth/instance rasters and object boxes, without room areas or mesh topology. The documented ScanNet mesh, segmentation and aggregation paths are absent for all 41 ScanNet captures. No independent ScanNet++ room-area/mesh path is registered.

Command for these counts: `bash scripts/cpu.sh scripts/s1k2_audit.py`. BLOCKER.md names the missing source and search scope; out/S1K2_GT_AUDIT.json lists every excluded capture, checked path and input SHA256. Shared metadata indexes were filtered to registered train identities; held-out payloads and evaluation items were not opened.

Rebind: NOT PERFORMED. configs/KERNEL_PROVENANCE_S1K2.json records status MISSING and authorization pending orchestrator. Its intended origin is not a claim of completed selection. The original provenance and frozen constants remain byte-identical. OPERATOR.md, KIT_SPEC_room_pricing.md, GPU_NEED.json and ROOMKIT_REPORT.md state the blocked status.

Validation command: `bash scripts/cpu.sh scripts/s1k2_validate.py`. {tests['tests']} existing synthetic tests {tests['verdict']}; {tests['failures']} failures and {tests['errors']} errors. The CPU gate dry run {dry['verdict']}: it rejects the missing S1k2 provenance. The full suite and inference dry run remain unrun because they require forbidden evaluation inputs or a selected kernel. These checks do not validate a new kernel.

Result-generation command: `bash scripts/cpu.sh scripts/s1k2_delivery.py`. out/S1K2_RESULTS.json records MISSING scores, the exclusions and input hashes. No folds, bootstrap draws or family scores were computed.

Packaging command: `bash scripts/cpu.sh scripts/s1k2_package.py`. Deliver out/sb_rkfam.tar and out/sb_rkfam.tar.sha256; out/S1K2_PACKAGE.json records the archive digest and verification. The package contains the blocked kit, training-only audit and source; it excludes inherited archives and evaluation payloads. It is not a launch-ready kernel package.

This task used zero GPU-hours and no network, SSH, Git or process termination. It wrote only in the workspace. Supply an authenticated scan-GT room-area source on local disk to unblock selection. The legacy-origin disclosure is retained because the task explicitly requires it.
'''
    assert len(report.splitlines()) <= 60
    (W/'out/S1K2_REPORT.md').write_text(report)
    (W/'out/ROOMKIT_REPORT.md').write_text(report)
    status('S1k2 is BLOCKED: independent scan-GT room areas are MISSING for all 110 registered training captures (102 rooms). Four candidate families are preregistered; no scores or kernel rebind exist. Eleven synthetic tests pass and the CPU gate rejects missing S1k2 provenance. The report and exclusions are complete; the delivery is a blocker package, not an approved kernel.')


if __name__ == '__main__':
    main()
