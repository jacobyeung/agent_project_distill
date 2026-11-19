"""Publish the build-21 result, preserving required phase and review evidence."""
import ast
import json
from pathlib import Path
import re
import subprocess

W = Path(__file__).resolve().parent
L = W.parents[1]
O = L / 'out'
LOG = O / 'tests/port21'
prior = (O / 'REPORT.md').read_text()
note = (O / 'NOTE_FOR_TREE_REBUILD.md').read_text()
(W / 'REPORT.before.md').write_text(prior)
(W / 'NOTE.before.md').write_text(note)
manifest = json.loads((O / 'patches_b21/manifest.json').read_text())
summary = json.loads((LOG / 'suite_summary.json').read_text())
audit = json.loads((LOG / 'artifact_audit.json').read_text())
now = subprocess.check_output(['date', '-u'], text=True).strip()
assert all(row['exit'] == 0 for row in summary)
assert (LOG / 'known_failure_comparison.txt').read_text().startswith('PASS:')
switches = note[note.index('| Switch |'):note.index("\n\nPatch 03's estimate")]
commands = '''```bash
patch --batch --fuzz=0 --no-backup-if-mismatch -p1 -i "$L/out/patches_b21/03_checkpoint_verify_memo.diff"
patch --batch --fuzz=0 --no-backup-if-mismatch -p1 -i "$L/out/patches_b21/04_launch_phase_timing.diff"
patch --batch --fuzz=0 --no-backup-if-mismatch -p1 -i "$L/out/patches_b21/02_parallel_frame_sha.diff"
```'''
new_note = '''## Build 21 port

Apply after N's first proof, in order **03, 04, 02**, to build 21 seal `b262e7a7`. Verify [patch hashes and base/result pins](patches_b21/manifest.json). Each patch also applies standalone. All hunks match exactly: zero fuzz, no offsets, no manual changes. No `.orig` or `.rej` remains in the verified trees.

''' + commands + '''

Rebuild and rescan the kit, executable inventory and source/config seals before launch. Keep every switch OFF for the normal proof. Enable candidates separately in this order:

''' + switches + '''

Patch 03's expected saving is **about 4–5 min (inferred)** per resume launch; **up to about 9 only if the page cache does not keep the checkpoint**. Four `complete()` calls explain measured guard envelopes of 675 and 86 seconds. The memo removes three warm passes. Set `TK_LAUNCH_TIMING=1` on the first resume job to measure the real saving.

OFF byte-identity checks pass before ON tests. All five patch scripts pass on build-21 copies: 66 tests, including 42 patch-01 tests in a separate diagnostic tree. The delivered three-patch set has 24 passing patch tests. Its native gate has 75 passes and 11 explicit skips, with matching baseline and switches-ON results. The skips are ten Gloo tests and one unstaged authenticated-pool test; the [report](REPORT.md#lane-tests-and-remaining-work) names them and gives the lane command. Five additional admission-fixture failures reproduce unchanged on baseline and patched build 21. Exact commands and outputs: [build-21 evidence index](tests/port21/INDEX.md).

**01 stays OFF**: it cannot hit in the production topology in a way that avoids native work. It is excluded from `patches_b21`. Its estimated saving is zero or worse. Mode p measured 140.57 and 145.27 minutes; the [cross-run design](CROSS_RUN_STORE_DESIGN.md) budgets about 70 minutes of potentially avoided prepare work before adoption costs. Its [Orchard reuse-floor measurement](MEASURE_NATIVE_REUSE.md) remains unrun. Preserve all native authorization, parent, checkpoint and all-rank first-step gates.

'''
new_note += note[note.index('## Review round 2:'):]
(O / 'NOTE_FOR_TREE_REBUILD.md').write_text(new_note)

parts = ['''VERDICT: DONE Build-21 patches 03, 04 and 02 apply with zero fuzz and pass OFF-identity, patch and native CPU checks; ten Gloo tests and one pool-fixture test remain for the lane.

## Build 21 port

The delivery is [patches_b21/manifest.json](patches_b21/manifest.json), in order **03, 04, 02**, against seal `b262e7a757d93e2485a523765916507b2bf3305fe3213cffca100007d19f2ce8` (936 files, measured and verified). Each patch applies independently and in that order with `patch --batch --fuzz=0 --no-backup-if-mismatch -p1`. The [handover](NOTE_FOR_TREE_REBUILD.md) has the exact commands and switch table. Every switch defaults OFF. **01 stays OFF**: it cannot hit in the production topology in a way that avoids native work; it is excluded from this delivery.

No hunk moved or failed. Build 21 preserves all five production files touched by these patches, so the three regenerated diffs are byte-identical to the reviewed build-20 diffs. The manifest pins build 21 rather than build 20. The recommended tree differs in exactly five production files and three added test scripts; no `.orig` or `.rej` files remain. Input bytes remain unchanged.

| Patch | Production hunks moved / failed | Bytes | SHA256 |
|---|---|---:|---|
''']
for name, entry in manifest.items():
    parts.append(f'| [{name}](patches_b21/{name}) | 0 / 0 | {entry["bytes"]} | `{entry["sha256"]}` |\n')
parts.append(f'''
Started Thu Nov 19 10:36:04 UTC 2026 on `trinity-1-18`; deadline 11:51:04 UTC. This report was assembled at {now}. The artifact audit measured workspace size **{audit['workspace_bytes_measured']:,} bytes** and scratch free space **{audit['scratch_free_bytes_measured']:,} bytes**. No production speedup was measured. Patch 03's estimate is **about 4–5 min (inferred)** per resume launch; up to about 9 only if the page cache does not keep the checkpoint. Patch 04 saves no time directly; patch 02 needs an isolated warm-storage measurement.

## Exact build-21 commands and results

The five OFF checks ran first. They compare baseline and patched checkpoint/frame verdicts and fixture bytes, job and recursive-run command traces and stdout/stderr, and real `c.sh` stage output/steps bytes. The job and run checks cover successful dispatch and an exit-7 guard failure with switches unset and explicitly zero. The dedicated stage check runs OFF only. Its exact result is `Ran 5 tests in 2.809s`, `OK` ([output](tests/port21/off_identity.txt)).

```bash
source work/fix2_env.sh
export TMPDIR="$L/work/port21/tmp" TEST_TMP_ROOT="$L/work/port21/tmp" LANE_TEST_OUTPUT="$L/work/port21/tmp"
nice -n 10 "$PY" -I -s -B work/port21/check_off.py work/port21/recommended
nice -n 10 "$PY" -I -s -B work/port21/run_suites.py
nice -n 10 "$PY" -I -s -B work/port21/check_known_failures.py out/tests/port21
nice -n 10 "$PY" -I -s -B work/port21/audit_delivery.py
```

`PY=/scratch/jjyeung/envs/p1cpu/bin/python`. The runner sets CUDA empty, bytecode disabled, OMP/MKL/OpenBLAS threads to eight, tokenizer parallelism false, all test/cache paths inside this workspace, and `SO_NO_LOCAL_SOCKETS=1`. Torch tests set `torch.set_num_threads(8)` before test work. Tests execute serially under nice 10. Every log below contains the exact command, working directory, environment, stdout/stderr and exit code. [INDEX.md](tests/port21/INDEX.md) also links application and audit evidence.

| Tree / script | Exact output summary | Full command and output |
|---|---|---|
''')
for row in summary:
    path = Path(row['output'])
    lines = [line for line in path.read_text().splitlines() if line.startswith(('Ran ', 'OK', 'FAILED'))]
    parts.append(f'| `{row["label"]}` | ' + '; '.join('`' + line + '`' for line in lines) + f' | [log](tests/port21/{path.name}) |\n')
parts.append('''
The delivered set has **24 patch tests + 86 native tests: 99 pass, 11 skip**. The diagnostic combined tree also applies the unchanged patch 01 solely to rerun its two scripts: **66 patch tests + 86 native tests: 141 pass, 11 skip**. Patch 01's tests do not establish a production cache benefit. The five OFF comparisons and five extra probes pass separately. Repeated baseline/ON/standalone runs are shown individually rather than counted as new test coverage.

The additional native admission-fixture comparison reproduces the same four failures and one error on baseline and patched build 21. Both 92-test attempts exit 1; the comparison exits 0. Exact outputs: [baseline](tests/port21/known_native_failures_input.txt), [patched](tests/port21/known_native_failures_patched.txt), [matching identities](tests/port21/known_failure_comparison.txt). These fixture failures remain outside the supported 86-test gate; they are not counted as passes.

The retained [OFF harness error](tests/port21/off_identity.harness_error.txt) records two Python indentation errors in extracted fixture methods. The corrected harness passes before any ON suite runs. No production code changed to address these errors.

## Lane tests and remaining work

Sockets are unavailable by dispatch; this run does not attempt them. The native runner explicitly skips the whole `tests.test_s1_checkpoint_buffers.CheckpointBufferTests` class because its `setUpClass` starts a real TCP/Gloo process group. The lane still needs these ten tests:

''')
module = ast.parse((W / 'baseline/tests/test_s1_checkpoint_buffers.py').read_text())
methods = sorted(node.name for node in ast.walk(module) if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'))
parts.extend('- `' + name + '`\n' for name in methods)
parts.append('''
The eleventh skip is `tests.test_s1_launch_kit.LaunchKitTests.test_packaged_templates_validate_but_do_not_authorize_execution`: its authenticated pool selection is not staged. With sockets and the authenticated fixtures available, rerun the same gate without the sandbox skip:

```bash
SO_NO_LOCAL_SOCKETS=0 nice -n 10 "$PY" -I -s -B "$L/work/run_native_regression.py" "$L/work/port21/recommended"
```

READY names `work/base/tree_b01ce449`, `work/build15/inputs` and `work/build_n1/inputs` for the lane's separate focused suites. The exact read-only source paths are recorded and linked under `work/port21/fixtures/work` ([mapping](tests/port21/fixture_links.json)). The bounded 86-test native gate does not consume those links. This run does not claim to reproduce READY's separate 112-test proof.

The lane must rebuild/rescan and reseal the kit, run its socket/pool tests and preserve all native training gates before launch. No Orchard job, GPU validation or production launch timing ran here. The Orchard complete-journal reuse-floor measurement in [MEASURE_NATIVE_REUSE.md](MEASURE_NATIVE_REUSE.md) remains unrun; the separate cross-run store implementation, two-node checks and admission review are outside this port. These pending production checks do not change the completed build-21 port result.

## Risks and detection

Patch 03 assumes completed checkpoints remain immutable under cooperating writers. Stat metadata is not authentication against a same-user forger or a guarantee of immediate timestamps for arbitrary mmap writes. The extra probes force rehashing after chmod, refuse writes during hashing and disable hits under symlinked parents. Check `.checkpoint-verification/<job>.events.jsonl`; missing events mean no demonstrated memo benefit. Native loaders still verify SHA256 before loading shards, replicated data and RNG (`work/port21/baseline/student_pilot/full_ft.py:563,603,618`; `carrier_c1_run.py:2069`).

Patch 02 hashes every byte, caps workers at eight and pending work at twice the worker count; storage contention can make it slower. Fault and bounded-work probes pass. Measure f2 alone before enabling it. Patch 04 writes timing only; missing or unwritable logs cannot abort a launch. OFF behavior is verified on synthetic fixtures, not a full Orchard run. The five native admission-fixture failures require fixture repair and a lane rerun, not relaxed production checks.

No Git, SSH, Slurm, GPU, paid API, production job, file deletion or external write ran. All source copies and test outputs remain in this workspace; READY fixture targets remain read-only. No other agent's work was stopped.

## Framework evidence

The installed Torch version is `2.11.0+cpu` (`/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/version.py:4`). CPU intra-op thread control and its required placement before test work are documented at `torch/_torch_docs.py:9814–9824` in that installation and in the [official PyTorch 2.11 set_num_threads documentation](https://docs.pytorch.org/docs/2.11/generated/torch.set_num_threads.html).

The skipped fixture opens a local socket and calls `init_process_group('gloo', init_method='tcp://…')` (`work/port21/baseline/tests/test_s1_checkpoint_buffers.py:28–35`). Installed `torch/distributed/rendezvous.py:190–207,210–237` constructs its TCPStore. The [official TCP initialization documentation](https://docs.pytorch.org/docs/2.11/distributed.html#tcp-initialization) describes the network rendezvous. No socket-dependent test is counted as passed.

''')
# Keep the original task's measured phase/input analysis and explicit review mappings.
parts.append(prior[prior.index('## Measured phases and preparation inputs'):prior.index('## Risks, remaining work and detection')])
parts.append('\nThe requested review-round mappings and the harness-error disclosure are retained as audit evidence; these are deliberate exceptions to the no-archaeology writing rule.\n')
(O / 'REPORT.md').write_text(''.join(parts))

index = ['# Build 21 evidence\n\n', 'All paths below contain exact output, not inferred results. Tests use build 21 seal `b262e7a7`.\n\n',
         '- [OFF comparisons](off_identity.txt) ran before ON suites; [retained harness-error output](off_identity.harness_error.txt).\n',
         '- [Machine-readable test commands and exits](suite_summary.json).\n',
         '- [Ordered delivered-patch application](recommended.apply.txt).\n',
         '- [Artifact audit](artifact_audit.json): complete base/result identities, patch scope, syntax, size and backup checks.\n',
         '- [Known native fixture comparison](known_failure_comparison.txt).\n',
         '- [READY read-only fixture links](fixture_links.json).\n\n']
for name in manifest:
    index.append(f'- [{name}: initial build-20 patch trial]({name}.initial.txt); [fresh build-21 delivery application]({name}.delivery.txt).\n')
index.append('\n')
for row in summary:
    index.append(f'- [{row["label"]}]({Path(row["output"]).name}), exit {row["exit"]}.\n')
(LOG / 'INDEX.md').write_text(''.join(index))
print('Published build-21 report, handover and evidence index at ' + now)
