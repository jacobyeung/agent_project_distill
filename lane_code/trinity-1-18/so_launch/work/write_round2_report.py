"""Write the current delivery report from retained evidence, without Git."""
from pathlib import Path
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'out'
LOGS = Path((ROOT / 'work/round2_logs.txt').read_text().strip())
STAMP = LOGS.name
records = json.loads((LOGS / 'summary.json').read_text())
manifest = json.loads((OUT / 'patches/manifest.json').read_text())
old = (ROOT / 'work/review_round2_before/out/REPORT.md').read_text()
body = old[old.index('## Measured phases'):old.index('## Review round 1:')]
body = body.replace('**Estimate: 4–10 min per resume launch**, inferred rather than benchmarked.',
    '**Estimate: about 4–5 min (inferred); up to about 9 only if the page cache does not keep the checkpoint**.')
start = body.index("C' spent **675 s**")
end = body.index('\n\nPatch 03 binds', start)
body = body[:start] + '''C' spent **675 s** between preflight PASS and first stage prep, covering three checks, and **86 s** between p exit and second stage prep, covering one. A had no checkpoint and one second in each gap (`look1.out:280–281,347–348`). The node reports 1842 GiB RAM (`last.txt:163`), which makes page-cache retention plausible but does not measure cache residency. Subtracting that one-second baseline gives an inferred warm pass of about 85 s. Removing three warm passes saves about 255 s, or **about 4–5 min (inferred); up to about 9 only if the page cache does not keep the checkpoint**. The conditional upper estimate is 2 × (675 / 3) + 86 = 536 s, assuming the first pass is at least as slow as each later pass. It is not a throughput measurement.

Set `TK_LAUNCH_TIMING=1` on the **first resume** job and retain the four guard envelopes and `.checkpoint-verification/<job>.events.jsonl`. The four-process CPU regression exercises real `g.py.persistent_launch` and the direct chooser; it records `[false, true, true, true]` memo hits and refuses a subsequently corrupted payload. Its tiny fixtures do not measure checkpoint throughput.''' + body[end:]
body = body.replace('The native preparation path also has mutable journal state.',
    'Cache metadata uses a key and per-component SHA256 digests; full components remain in memory for key construction. Schema v2 refuses v1 cache entries. Native prepared/config files remain byte-preserved.\n\nThe native preparation path also has mutable journal state.')

head = '''VERDICT: PARTIAL Findings 1–7 have code or design fixes and passing CPU regressions; the required Orchard reuse-floor measurement remains unavailable under this dispatch.

Patch 03 ranks first; application order is **03, 04, 02** after N's first proof and a rebuilt, rescanned kit. Every switch defaults OFF. **01 stays OFF: it cannot hit in the production topology in a way that avoids native work.** Its estimated production saving is zero or worse. No production speedup was measured.

The builder fixes `run_directory=/tmp/jjyeung/okit_8865619b/runs/<run_key>` (`in/tree/work/tree_r1/launch_s1/build.py:221`); `b/g.py:66` requires node-local run storage. A complete same-node journal already supports native reuse. Another node lacks the source; another logical run changes the config/key. Defensive relocation fixtures do not establish a useful production HIT.

The [so_xstore design](CROSS_RUN_STORE_DESIGN.md) specifies external GCS sessions, verified login-node cache publication, portable phase identities and exact derived-config/preparation checkpoint bindings. Its planning estimate is **about 70 min, the prepare half, until measured**, before fetch, full SHA and adoption costs. Node-local frame work remains necessary. Estimated effort is **13–22 engineering days plus 1–2 reviewer-days**. This package neither implements nor approves the store.

'''
mapping = '''## Review round 2: finding -> fix -> test

| Finding | Fix | Regression evidence |
|---|---|---|
| 1 MEDIUM: unsupported adoption saving | Budget only the prepare half; explicitly retain node-local frame audit and the unmeasured complete-journal floor. | Planning/design contract fails on the reviewed text and passes now. [Native measurement procedure](MEASURE_NATIVE_REUSE.md) is delivered but **not run**: no Orchard access or production journal is authorized here. |
| 2 MEDIUM: missing Orchard data channel and identity work | Specify external GCS session issuance, candidate verification/root publication, login-node read-only cache, zero-write job staging, content-derived phase names and exact config/preparation binding; re-estimate effort. | Transport/identity design contract fails before and passes after. This checks design requirements, not a store implementation. |
| 3 LOW: unsupported memo range | Infer three warm passes from the 86-s envelope and 1-s no-checkpoint baseline; state the conditional 536-s upper estimate. | Report/note contract fails before and passes after; four-process guard/chooser regression passes. Production timing remains pending. |
| 4 LOW: real stage-lock timing untested | Execute whole real `c.sh` under `bash -euo pipefail`, with only staging dependencies stubbed. | Coverage contract fails on the reviewed tests and passes now. Prep/preflight ON emit exactly two lock lines and exit 0; OFF output equals input byte for byte. The implementation already worked; the defect was coverage. |
| 5 LOW: offset hunks leave inventory-visible backups | Apply with `--no-backup-if-mismatch` in the note, manifest and verifier. | The documented all-four application leaves `.orig` files before; the same order leaves no `.orig` or `.rej` after. Fresh standalone, recommended and combined trees pass. |
| 6 LOW: inherited `TK_PC_LOCK_HELD=1` skips lock | Export `TK_PC_LOCK_HELD="$$"`; a child accepts it only when it equals `$PPID`. Keep `flock -w 600 7 || exit 75`. | Inherited `1` bypasses contention before; t/u with unset, `1` or stale-PID markers exit 75 after. Recursive and symlink-parent runs still succeed; concurrent preparation remains serialized. |
| 7 LOW: full config copies and method-bearing refusal | Store only key/component digests; compare them on restore. Use generic optional-input errors and catch context refusal before restore starts. | Two new tests fail before and pass after: a method-bearing valid config publishes/restores without copying its fields, changed component digest refuses, and the CLI safely misses without method text or traceback. |

Exact before/after outputs and commands are indexed in [review_round2/INDEX.md](tests/review_round2/INDEX.md). The full final suites include every earlier behavior regression. Documentation and coverage contracts are explicitly distinguished from runtime failures.

## Review round 1: finding -> fix -> test

| Finding | Current invariant and rerun evidence |
|---|---|
| 1 | 01 OFF; production-path/design contract and same-path/purge tests pass. |
| 2 | MISS leaves partial/foreign journals untouched; native reuse/refusal, copy/install failure and report-error tests pass. |
| 3 | 03 first; all four real guard/chooser calls pass with one full verification. |
| 4 | Parent-bound lock marker and 600-s request; symlink, duplicate t/u and concurrent-job tests pass. |
| 5 | Whole real `c.sh` HIT/MISS/error/missing-root matrix passes. |
| 6 | Missing/unwritable timing logs cannot abort; recursive/parent guard events and exit-7 behavior pass. |
| 7 | Full launch-kit, production-import and checkpoint-buffer modules are selected; explicit environment skips appear below. |
| 8 | Unused environment names do not change the key; written cache metadata uses generic component names and digests. |

## Risks, remaining work and detection

The Orchard complete-journal measurement required by finding 1 remains **not done**. This dispatch is confined to trinity-1-18, forbids SSH/Slurm and has no complete production journal. The supplied procedure preserves native hashes and refuses cold phases; use it only in the authorized Orchard namespace with matching CPU bindings and approved full-rehash I/O. This outstanding measurement is why the verdict is PARTIAL. No other HIGH, MEDIUM or qualifying LOW finding is deferred. The review contains no HIGH findings.

The separate so_xstore build owns implementation, two-node determinism, cross-node adoption/restore, transport authorization and independent admission review. Its runtime and effort numbers are estimates. Checkpoint bindings still pin the derived config and preparation receipt; a path or seal change must refuse resume. Preserve native authorization, frame, parent, checkpoint and all-rank first-step gates.

Patch 03 assumes cooperating writers leave completed checkpoints immutable. Its stat guard is not authentication against a same-user forger or a proof of immediate timestamps for arbitrary mmap writes. Reproduced probes force full hashing after chmod, refuse a write during verification, and disable memo hits under a symlinked parent. Check the events file; missing events mean no demonstrated memo benefit. Native loaders still SHA-check shards, replicated payload and RNG before deserialization (`student_pilot/full_ft.py:563–567,603,618`; `carrier_c1_run.py:2063`).

Patch 02 still hashes all bytes and may lose time under storage contention. CPU probes confirm verdict/count parity on deterministic randomized corrupt/missing fixtures and at most twice the worker count outstanding. No production throughput improvement is claimed. Patch 04 adds timing only. OFF-path CPU tests check native command/output behavior, including byte-identical real-stage output. Patch 01 remains OFF despite its defensive fixes; its self-hashed index does not authenticate a hostile writer, and its parent-PID marker prevents accidental inheritance rather than same-user forgery.

This sandbox rejects socket creation with `PermissionError: [Errno 1] Operation not permitted`. A native attempt confirms that checkpoint-buffer `setUpClass` cannot start. The supported gate explicitly skips those ten Gloo tests plus one unstaged authenticated-pool test. The reviewer reports Gloo success in its own environment; this run does not count that as reproduced evidence. Five native admission-fixture failures match exactly on input and patched trees, so they remain an input-fixture limitation.

No Git, SSH, Slurm, GPU, paid API, production job, heavy dataset I/O or file deletion ran. No other agent's work was stopped. Tests retain small local fixtures, hide CUDA and inherit nice level 10 and eight-thread CPU library limits. The failed socket attempt was an environment refusal, not a cluster-killed job. Network access read only official library documentation.

## Framework evidence

Installed Torch reports `2.11.0+cpu` at `/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/version.py:4`. Its CPU intra-op thread control is documented in that installation's `torch/_torch_docs.py:9814–9824`; every Torch test calls `torch.set_num_threads(8)` before test work. The same behavior is described by [PyTorch 2.11 set_num_threads](https://docs.pytorch.org/docs/2.11/generated/torch.set_num_threads.html). This is a CPU validation run, not CUDA 12.9/H100 validation.

The native checkpoint-buffer fixture calls `init_process_group('gloo', init_method='tcp://…')` (`tests/test_s1_checkpoint_buffers.py:28–32`). Installed `torch/distributed/rendezvous.py:190–207,210–237` constructs its TCPStore and `distributed_c10d.py:1605` implements process-group setup. [PyTorch 2.11 distributed documentation](https://docs.pytorch.org/docs/2.11/distributed.html#tcp-initialization) describes that TCP rendezvous. Socket refusal prevents this fixture before any checkpoint behavior executes.

## Exact commands and results

'''

def summary(path):
    return '; '.join('`' + line + '`' for line in path.read_text().splitlines()
                     if re.match(r'^(Ran \d+ tests? in |OK(?: |$)|FAILED)', line))

exact = f'Final fresh-patch verification: **{STAMP}**. Report assembled at {subprocess.check_output(["date", "-u"], text=True).strip()}.\n\n'
exact += '''Every patch applies independently with `--fuzz=0 --no-backup-if-mismatch`. Recommended order is 03, 04, 02; combined adds 01 last with its switch OFF. Offset hunks are accepted only when exact context matches; no fuzz, rejected hunk or backup file is accepted. Manifest entries pin each input/result file, the complete base-tree digest, patch SHA256/bytes and native-gate SHA256.

```bash
source work/fix2_env.sh
SO_NO_LOCAL_SOCKETS=1 nice -n 10 "$PY" -I -s -B work/verify_delivery.py
```

`work/fix2_env.sh` selects `/scratch/jjyeung/envs/p1cpu/bin/python`, sets `CUDA_VISIBLE_DEVICES=''`, `PYTHONDONTWRITEBYTECODE=1`, OMP/MKL/OpenBLAS threads to 8, disables tokenizer parallelism, and keeps TMPDIR/TEST_TMP_ROOT/LANE_TEST_OUTPUT inside this workspace. The verifier gives each fresh tree its own fixture paths. Exact per-test commands, stdout/stderr and exit statuses are retained below.

| Application | Exact test summaries | Command/output |
|---|---|---|
'''
for row in records:
    path = Path(row['log'])
    exact += f"| {row['name']} | {summary(path)} | [log](tests/{STAMP}/{path.name}) |\n"
exact += '''
The combined run registers **152 tests: 141 pass and 11 skip** (66 patch tests and 86 native tests). The recommended set registers 110 tests: 99 pass and 11 skip. Skips are never counted as passes.

Additional runs use the same CPU environment:

| Check | Exact test summaries | Output |
|---|---|---|
'''
for label, name in [('Native input baseline', 'native_input.txt'),
                    ('Native recommended, 02–04 ON', 'native_recommended_on.txt'),
                    ('Input with known admission fixture', 'known_native_failures_input.txt'),
                    ('Combined with known admission fixture', 'known_native_failures_patched.txt'),
                    ('Review metadata/frame probes', 'review_extra_probes.txt')]:
    exact += f'| {label} | {summary(LOGS / name)} | [log](tests/{STAMP}/{name}) |\n'
for label, name in [('Round 1 delivery contracts', 'round1_contracts.after.txt'),
                    ('Round 2 delivery contracts', 'delivery.after.txt')]:
    exact += f'| {label} | {summary(OUT / "tests/review_round2" / name)} | [log](tests/review_round2/{name}) |\n'
exact += f'''
The known-failure comparison exits 0 after confirming the same five identities; its two 92-test runs intentionally exit 1. Exact comparison output:

```text
{(LOGS / 'known_failure_comparison.txt').read_text().rstrip()}
```

The initial unskipped native attempt is retained in [socket attempt](tests/20261119T094816Z/recommended.txt): `Ran 76 tests` and `FAILED (errors=1, skipped=1)`, with the Gloo class blocked at socket creation. Its four standalone patch suites already passed. The final run uses explicit environment skips, without changing native tests or bypassing their assertions.

Full supplemental commands are in [commands.txt](tests/{STAMP}/commands.txt). Phase arithmetic was regenerated from the supplied timestamps; its exact output is [phase_arithmetic.txt](tests/{STAMP}/phase_arithmetic.txt). Delivery contracts and final artifact checks are indexed in [review_round2/INDEX.md](tests/review_round2/INDEX.md). All earlier relevant fixes are rechecked by these current runs, not assumed from an earlier model's verdict.

| Patch | Bytes | SHA256 |
|---|---:|---|
'''
for name, entry in manifest.items():
    exact += f"| [{name}](patches/{name}) | {entry['bytes']} | `{entry['sha256']}` |\n"
exact += f"\nBase-tree pin: `{next(iter(manifest.values()))['base_tree_sha256']}`. See [manifest.json](patches/manifest.json) for the exact hash encoding and per-file base/result pins. [Final artifact audit](tests/final_artifact_audit.txt) checks fresh-tree identities, shell/Python syntax, counts, before/after source identity, document links, workspace size and output checksums.\n"
exact += '\nThe required review-round mappings are retained as audit evidence; this is the deliberate exception to the no-archaeology writing rule.\n'
(OUT / 'REPORT.md').write_text(head + body + mapping + exact)
print('Wrote REPORT.md with exact summaries from', LOGS)
