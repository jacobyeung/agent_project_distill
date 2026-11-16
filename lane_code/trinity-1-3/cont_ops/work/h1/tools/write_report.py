"""Write the current packet report from validated artifacts."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
load=lambda p:json.loads((H/p).read_text())
ids=load('ids.json');up=load('UPLOAD.json')
proof=load('evidence/cpu/fallback_fix4/result.json');tok=ids['tokens'];o='/project/community/jjyeung/okh7';bun=o+'/i_'+tok['store'];kh=o+'/x_'+tok['kit'];rs=o+'/r/'+tok['root']
rows=[('Configuration identity',ids['identity'],'Unchanged: training settings and code remain pinned.'),('Admission contract',ids['contract'],'Unchanged: native admission requirements remain pinned.'),('Trainer tree',ids['tree'],'Pinned trainer inventory.'),('Trainer archive',ids['trainer']['sha256'],'Deterministic archive matches its pin.'),('Code pin',ids['code_pin'],'Unchanged: trainer inventory and closures match.'),('Fixture manifest',ids['fixture_manifest'],'Pinned isolated runtime and authorization.'),('Authorization',sha(H/'payload/4.json'),'Pinned conditional authorization.'),('Deriver',sha(H/'tools/derive_kit_h1.py'),'Manifest-scoped copying and mode checks exclude all runtime state.'),('Batch wrapper',sha(H/'runtime/jb.sh'),'Pinned private root and foreign-run refusal.'),('Upload archive',up['sha256'],'Changed: manifest-scoped source reads, copies and mode comparisons.')]
report=f'''The H1-1 packet derives successfully from a fixture with all 193 real Orchard source entries and their sealed permissions and passes the CPU checks. It remains unauthorized for submission. The fixed four-rank stop chain is prepared for an operator rerun; it was not executed in this sandbox. No Orchard, network, SSH, GPU, Git or deletion command ran.

H1-1 starts from step 544, retains D0’s rows, seed 17, world size 4 and 1,000-step learning-rate horizon, enables S1/S2, and exports at 100 and 200. Its normal terminal status is `H1_STOP` with `stopped_for_resume=false`. The registered answer-difference rule can end it at 100 if the share over steps 1–50 exceeds 35%.

| Item | Value |
|---|---|
| Run | `{tok['run']}` |
| Deployment kit | `{kh}` |
| Upload bundle | `{bun}` |
| Persistent slot root | `{rs}` |
| Job name | `{ids['job_name']}` |
| Node-local root | `/tmp/jjyeung/a_17c4ffa4` |
| Node-local output | `/tmp/jjyeung/a_17c4ffa4/runs/17c4ffa4` |
| Logical and GCS namespace | `8865619b` |
| Allocation | `advanced`, one node, four GPUs, 48 CPUs, 800G, 13 hours |

The per-run root contains staging, namespace mounts, preflight jobs, training jobs, runs and upload archives. `c.sh` keeps the sealed logical prefixes and GCS namespace. `jb.sh` refuses any foreign entry in that root’s `runs/` before creating directories. D0’s kit, outputs, sessions and identity remain untouched. The inherited eight-GPU helper `b/jt8c.sh` is not called by this packet’s entry chain (`s.sh → jb.sh → job.sh → p0.sh/r.sh`).

**Deliverables and hashes**

| Artifact or identity | SHA256 | Reason |
|---|---|---|
'''
report+=''.join(f'| {n} | `{h}` | {why} |\n' for n,h,why in rows)
report+=f'''
The job name is exactly `a15_cot_ap5ee9da63`: the account-mandated opaque prefix `a15_cot_ap` plus token `5ee9da63`. Configuration identity, admission contract, trainer archive, fixture manifest and batch wrapper remain unchanged. [evidence/hash_changes_fix4.json](evidence/hash_changes_fix4.json) records the affected hashes. `DIFF.md` describes the implementation; `FIX4.md` records the local test results.

The trainer archive has {ids['trainer']['bytes']:,} bytes and 796 regular files. Its sorted inventory, mode/owner/time metadata and SHA256 match the independent rebuild. The derived fixture also matches a second derivation byte for byte. The new upload is `build/{up['archive']}` ({up['bytes']:,} bytes); `orch_h1.sh` has {up['script_bytes']:,} bytes. Each upload form stays below 20 MB. `UPLOAD.json` records every carried member; `SHA256SUMS.txt` seals the packet and current evidence.

The config key remains `{ids['config_key']}`. Review approval changes the config’s admission pin and may change its filename, while its identity and native admission contract remain fixed. The complete source kit is missing two payloads locally: `k/np226_5204b3a0.tar` and `k/t_e6456bcecb8d4a8f4f68158eb68275f8befff128.tar`. Their sealed hashes remain in every fixture manifest. Complete derivation refuses their absence; the login procedure must verify complete empty-override reproduction.

**Naming and permissions**

Every executable entry checks that `{o}` is a real directory with mode 0700. A mismatch prints the exact `chmod 700` fix command and exits before writing. The scripts use `umask 077`, create private BUN/KH/slot directories, verify their modes, and reject symlinks at those checked paths. Derive creates KH with mode 0700 and verifies it again after the final derive.

`g.sh` invokes `r.py copy`, which reads the routing archive location from the SHA-verified sealed deployment record inside Python. No new process argv contains that inherited source path. It copies to `BUN/a_b8b60bce.tar`, compares the stream SHA256 against a complete readback, and verifies every regular member against the sealed member pins before writing `a.json`. `g.sh` rechecks that archive digest before extraction and verifies the receipt/SQLite pins afterward. The sealed record has no whole-archive SHA256, so the copied archive digest is recorded at runtime; the pre-existing member hashes anchor its contents. No routing archive was copied on Orchard during this task.

The audit covers new argv/path/environment/log literals in the login scripts, `r.py`, the batch wrapper and added runtime lines. The local delivery filenames `orch_h1.sh` and `fin_h1.sh` are carried as script bodies; operators must not use those names as remote executable paths. New remote entrypoints are opaque (`o.sh`, `g.sh`, `z.sh`, `s.sh`, `r.py`, `jb.sh`). Trainer modules and the pinned room list remain inside private directories and archives; full private-content review is still required.

**Sealed-mode writes and validation**

The output writer grants owner-write permission only to an output file and its immediate parent, then restores both exact modes in `finally` blocks. It rejects links and paths outside the output root. Existing records retain their modes; new `k/` records and archives use the sealed `k/1.json` mode, while renamed configs use the original config mode. The SHA manifest retains the source manifest mode. Sealed ancestor directories retain their modes. Changed kits receive fresh empty 0700 runtime directories. Empty overrides copy only manifest members and their ancestor directories. The source certificate is outside the manifest and is never read or copied; every output receives an UNREVIEWED certificate.

`d.py` routes runtime patches, archive/pin copies, generated config/launch/source records, checksums and the ANON record through that writer. `r.py` uses it for the temporary final launch and certificate replacement. Its other writes target the mutable bundle. `z.sh` only verifies checksums and dispatches `r.py`; `v.py` performs read-only staging checks. `SHA256SUMS.txt` and `v.py` do not encode or compare modes. Prepare and final compare modes only for SHA256SUMS.txt members, their ancestor directories and the root. The manifest file itself, certificates and runtime state are outside that mode scope. Both evidence records bind this inventory by digest.

`tests/test_sealed_modes.py` reproduces the round-2 `b/r.sh` PermissionError using the observed 0400 files and 0500 directories. It also exercises a fully sealed tree, including `k/`, all runtime patches, new files beneath 0500 directories, failure restoration, out-of-tree refusals and mode-only comparison failures. H1, D0 and empty overrides pass on both fixture variants. Empty overrides reproduce sealed members byte-for-byte and mode-for-mode; source snapshots remain unchanged.

Two unavailable sealed payloads use small stand-ins with a test-only manifest pin in the complete fixtures. The real incomplete source is tested separately and still refuses complete derivation. These fixtures prove permission handling, not availability of the missing production payloads. `evidence/fix4_sealed_modes.json` records the six sealed-mode derivations and entrypoint checks; `evidence/fix4/tests.json` records the eleven original and reviewer regressions. `evidence/fix4_listing.json` records the exact 193-entry fixture, its 90 runtime entries, the fix-3 failure, passing prepare/empty/final comparisons, and negative mode tests. Guards reject every unlisted source read, stat or traversal, including poisoned b/ and k/ records and a dangling runtime link. REVIEW4.md covers each login and preflight check. The chain runner and existing `chain_r1/` were not modified or executed in this task.

**Inherited visible names**

These sealed names remain unchanged. They are explicit inherited exposures, not claims that the whole sealed runtime is anonymous.

| Location | Inherited name and exposure |
|---|---|
| `build/fx/b/c.sh:11–13` | `R=/project/community/jjyeung/distill/okit`, `HX`, and `IN=$R/in`; inherited staging commands can expose the cache path in argv. |
| `build/fx/b/c.sh:102` | `models--Qwen--Qwen3.5-9B`; the base-model cache path is sealed. |
| `build/fx/b/c.sh:7–8`; `payload/g.sh:36–37` | The `/scratch/fsw/.../av_dataengine_cot/users/jyeung` and `/lustre/fsw/.../av_dataengine_cot/users/jyeung` prefixes identify pinned logical receipts and mounts. |
| `build/fx/b/c.sh:16–17` | `runs/aws128p_20261025` and `/home/jjyeung/6d00e578` are inherited runtime locations. |
| `build/fx/b/c.sh:429` | The inherited `gcsput.py split` operation keeps its command interface. |
| `build/fx/b/p0.sh:12–31` | The inherited preflight receives `IN` and emits sealed input locations in its inventory. |

**Validation**

The four original local checks (`test_derivation.py`, `test_gate_binding.py`, `test_staging.py`, and `run_fallback.py fallback_fix4`) and `test_stop_bridge.py` pass. D0 regression reproduces identity `80f4af947f0ca9edfac04041cf65e079edb92752618b2de6dc4078491a88f1ba` and contract `aaf2d7b045632f14d96cfc62adbf2a1eab5212d713ac6ebaed03c1b44309ca19`.

The copied reviewer checks pass: altered trees/rows/settings are refused; removing `add_k 4.json` is now refused before output creation; the native gate also rejects the reviewer’s stale-authorization fixture. The faithful gate passes at 0.95 and fails at 0.94 or without camera rows. Its executable returns 1 below threshold and 2 for unreadable input. Review/archive/staging approvals are mocked only in the binding tests; those fixtures do not authorize deployment.

`test_fix1.py` exercises all entrypoint permission refusals, private directory creation, the foreign-run refusal, all active physical roots (including preflight), the routing copy/hash/member checks, missing-authorization refusal, and the final identity assertion. It checks that `z.sh` and `s.sh` run `sha256sum -c sums.txt` before interpreting operator evidence; an altered checksum fixture is refused. `test_visible_names.py` audits the named scripts and added runtime lines, preserving the explicit sealed-prefix exceptions above and allowing `a15_cot_ap` only as the submitter’s job-name prefix before a hex suffix. Negative checks reject the prefix in paths, logs, environment values and other commands, and retain every forbidden-word check.

The CPU fallback completed 200 optimizer steps in {proof['run']['elapsed_seconds']:.2f} seconds, exported m100/m200, reported `stopped_for_resume=false`, and verified a {proof['slot']['bytes']:,}-byte slot with SHA256 `{proof['slot']['archive_sha256']}`. It uses the native tiny model, real checkpoint/export serialization, one rank and local collective stand-ins. It does not establish distributed GPU behavior.

The exact patched `on_stop` function writes the run-dir request, and a real bwrap namespace sees the same inode. The relay survives denied `/proc` reads. The four-rank CPU cases require the supplied operator runner:

```sh
bash /scratch/jjyeung/orch_n30/cont_ops/work/h1/tests/RERUN_CHAIN.sh
```

The runner refuses an existing `chain_r1/`, copies the fixed packet into that fresh local directory, verifies copied bytes, and runs `signal`, `fileonly`, `hfail`, and `full200` once each. It writes `chain_r1/evidence/cpu/<case>/result.json` and one PASS/FAIL line per case in `chain_r1/summary.txt`. A harness failure stops subsequent execution and records those cases as FAIL without retrying. The copied harness preserves the real wrapper suffix, job/runner/relay and training loop; it replaces admission/staging and GPU telemetry with CPU fixtures. Only shell/Python syntax was checked here; the runner and four-rank harnesses were not executed.

**Operator procedure**

1. Register the five rows from `ORCHARD_LEDGER_PENDING.jsonl` in the orchestrator’s `work/ORCHARD_LEDGER.jsonl` before any Orchard call. F2 remains an operator action because this task permits writes only inside this packet. No token was minted or registered remotely here.
2. Verify `sha256sum -c SHA256SUMS.txt`. Confirm no conflicting allocation, private parent mode 0700, and fresh BUN/KH/slot targets. The operator must rename `{bun}` to `{bun}.f2` before re-uploading; the target-exists refusal remains active. Carry `orch_h1.sh` as the authorized wrapper’s script body, or upload the hash-checked opaque tar and extract into a new mode-0700 BUN. The login script verifies its transport and immutable payload checksums.
3. `o.sh` derives the BLOCKED candidate, verifies identity/contract, reproduces the sealed manifest members and their directory modes with empty overrides, and records staging/archive checks. Run `g.sh` with an installed CPU `PY_GATE` and optional `BW_GATE`. Its faithful gate must pass and bind the original routing receipt.
4. Obtain independent PASS review in `BUN/review.json`, bound to this source, identity and contract. Keep `production_go_granted=false` in the conditional authorization. Its expiry remains 2026-11-26T00:00:00Z; the irrelevant canary-2 condition is removed.
5. Run `z.sh derive`. It rechecks immutable checksums, checks gate/review/staging evidence, derives KH, asserts its configuration identity, verifies mode 0700, and compares the complete byte manifest and manifest-scoped mode inventory with a fresh expected derivation. `review.json` and `staging.json` are mutable attestations and are excluded from `sums.txt`; both are hashed in the initial `UPLOAD.json`, validated semantically, and re-pinned into the final derivation. All executable files, config overrides and `4.json` remain checksum-pinned.
6. Review the exact final kit and external contents. Install a valid CLEAN `anon.json` certificate and run `z.sh certify`. The new source includes the identifying pinned room list; the packet does not manufacture a clean certificate.
7. Mint fresh create-only sessions for the 44 names in `EXPORT_OBJECTS.txt`; store them only at `KH/sess.json`, mode 0600. K remains `8865619b`; export keys use run `17c4ffa4`. Check node-local capacity (the inherited 3.8-TB guard) and project slot capacity (slot bytes plus 20 GB).
8. Obtain a separate GO bound to identity, contract, final manifest and wrapper SHA256. Run `s.sh`, which rechecks checksums and approval bindings before `sbatch`. It submits `a15_cot_ap5ee9da63` with the allocation above and USR1 3,600 seconds before timeout. Verify native admission, real first-batch/routing checks, terminal status, exports and the slot receipt.

Real routing identity, model/rows first batch, complete Orchard staging, distributed signal delivery under this fixed packet, GPU/NCCL behavior, production sessions and the inherited GCS fallback remain unverified. `4.json`, review/staging drafts and the GO template remain non-authorizing. No requested R1–R4 change was skipped.
'''
(H/'REPORT.md').write_text(report)
