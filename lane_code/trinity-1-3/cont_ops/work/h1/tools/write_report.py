import hashlib,json,tarfile
from pathlib import Path
H=Path(__file__).resolve().parents[1];D=H.parent/'d0'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
ids=json.loads((H/'ids.json').read_text());tok=ids['tokens'];up=json.loads((H/'UPLOAD.json').read_text());la=json.loads((H/'build/fx/k/launch.json').read_text());cfg=json.loads((H/'build/fx'/la['config']['file']).read_text())
proof=json.loads((H/'evidence/cpu/fallback_final/result.json').read_text());base='/project/community/jjyeung/okh7';bun=base+'/i_'+tok['store'];kh=base+'/x_'+tok['kit'];root=base+'/r/'+tok['root']
# Confirm all supplied extraction bytes; this does not read external data or model stores.
checks=[]
for a,dest in [('in/h1_1_kit_ready.tar','source'),('source/h1_1_code.tar','source/code'),('in/receipt_real_forced.tar','receipts')]:
 with tarfile.open(H/a) as tf:
  members=[m for m in tf if m.isfile()]
  assert all(hashlib.sha256(tf.extractfile(m).read()).hexdigest()==sha(H/dest/m.name) for m in members)
 checks.append(dict(archive=a,sha256=sha(H/a),files=len(members),extraction_matches=True))
for line in (H/'in/SHA256SUMS_inner').read_text().splitlines():
 digest,n=line.split('  ');assert sha(H/'source'/n)==digest
(H/'evidence/input_verification.json').write_text(json.dumps(checks,indent=2)+'\n')
report=f'''**H1-1 Orchard packet — prepared, not authorized for submission**

The packet derives a new code-tree kit from the sealed source kit. D0 regression, exact-field, source-inventory, deterministic-archive, stop-bridge, and CPU fallback checks pass. Production launch remains blocked on Orchard checks, independent review, content certification, fresh export sessions, and a separate GO. `4.json` keeps `production_go_granted=false`.

H1-1 warm-starts from step 544, retains D0’s rows, seed 17, world size 4 and 1,000-step LR horizon, enables S1 and S2, and exports at 100 and 200. It ends at 200 with `stopped_for_resume=false`. The registered answer-difference rule can instead end it at 100 when the share over steps 1–50 exceeds 35%.

| Item | Value |
|---|---|
| Run | `{tok['run']}` |
| Deployment kit | `{kh}` |
| Logical kit namespace | `8865619b` |
| Upload bundle | `{bun}` |
| Persistent slot root | `{root}` |
| Job name | `a15_cot_ap{tok['job']}` |
| Trainer output | `{cfg['output']}` |
| Preparation output | `{cfg['preparation_output']}` |
| Node-local output | `{la['run_directory']}` |
| Allocation | `advanced`, one node, four GPUs, 48 CPUs, 800G, 13 hours |

The new paths are not D0’s run, deployment kit, bundle or export-session paths. The deployment reads D0’s existing m544 archive and shared rows without modifying them. The donor artifact still names immutable `469ddece/m544` inputs; those are read pins, never this leg’s output paths.

**Deliverables and hashes**

`tools/derive_kit_h1.py` accepts one `code_tree` override with archive and code-pin file/SHA256 pairs, plus an optional archive attestation. It validates the complete sorted tar inventory, member safety, ownership, timestamps, modes and closure pins. It regenerates `7.json`, `s1_record.json`, deployment commit/trainer/record, config code pin, launch revision/source seal, archive record and manifest. READY additionally requires the new source/config authorization and an actual project archive attestation.

Config additions are restricted to the registered `h1` block, milestones [100, 200], and the two scheduled-sampling deltas in both locations. Other recipe, optimizer and deployment-code overrides remain refused. The runtime changes are fixed patches, not a general `b/` override. [DIFF.md](DIFF.md) explains every changed derivation-tool line and includes the exact trainer/runtime patches.

| Artifact or identity | SHA256 |
|---|---|
| Configuration identity | `{ids['identity']}` |
| Admission contract | `{ids['contract']}` |
| Trainer tree | `{ids['tree']}` |
| Trainer archive, `{ids['trainer']['file']}` | `{ids['trainer']['sha256']}` |
| Code pin, `payload/7.json` | `{ids['code_pin']}` |
| Local fixture manifest | `{ids['fixture_manifest']}` |
| Draft authorization, `payload/4.json` | `{sha(H/'payload/4.json')}` |
| Derivation tool | `{sha(H/'tools/derive_kit_h1.py')}` |
| Wrapper, `runtime/jb.sh` | `{sha(H/'runtime/jb.sh')}` |
| Upload archive, `build/{up['archive']}` | `{up['sha256']}` |
| Input outer archive | `{sha(H/'in/h1_1_kit_ready.tar')}` |
| Input code archive | `{sha(H/'source/h1_1_code.tar')}` |
| Supplied real-forced receipt archive | `{sha(H/'in/receipt_real_forced.tar')}` |

The trainer tar is **{ids['trainer']['bytes']:,} bytes**, contains 796 regular files, and reproduces exactly on a second build. D0 has 792 members. Both use sorted relative names, UID/GID 0, empty owner names, mtime 0 and 0644/0755 modes. Sealed member modes are preserved; the four added files use 0644. The R0 file has its supplied SHA256 and 372 rooms. The flat trainer archive contains `auth/R0_ROOMS.txt`; the patched resolver opens it there.

The upload archive is **{up['bytes']:,} bytes**; the self-contained upload script is **{up['script_bytes']:,} bytes**. Each carried file and both upload forms are below 20 MB. `UPLOAD.json` lists every carried file, size and hash. `SHA256SUMS.txt` covers the primary deliverables and evidence; `payload/sums.txt`, `build/fx/SHA256SUMS.txt`, `payload/7.json` and native checkpoint/export manifests cover their member inventories. `evidence/input_pins.json` records the exact D0 inputs.

The local draft config key is `{ids['config_key']}`. An independently signed review changes the config-file bytes/key through the admission pin, but does not change its identity or admission contract. The final READY manifest is generated and checked on Orchard; the local FIXTURE manifest is not a READY certificate.

**Validation and limits**

- `evidence/derivation.json`: D0’s own overrides reproduce identity `80f4af947f0ca9edfac04041cf65e079edb92752618b2de6dc4078491a88f1ba` and contract `aaf2d7b045632f14d96cfc62adbf2a1eab5212d713ac6ebaed03c1b44309ca19`. H1 changes exactly the requested training fields, output identities, code binding and admission pin. Nine forbidden-override cases are refused.
- Empty-override reproduction is locally limited by missing `k/np226_5204b3a0.tar` and `k/t_e6456bcecb8d4a8f4f68158eb68275f8befff128.tar`. A complete derivation correctly refuses them. Empty fixture derivation reproduces every present manifest member byte for byte except the two explicit FIXTURE safety fields in `launch.json`; both absent payload hashes remain in the manifest. The login script runs the complete empty-override comparison against Orchard’s sealed kit.
- `evidence/archive_layout.json`, `evidence/tree_changes.json` and the unchanged native `b/v.py` tree check verify the archive and all file pins. Seven tree members differ from D0, including the four additions. Runtime and operation import closures each contain 200 files and match the new code pin.
- `evidence/gate_binding.json` checks source/config/authorization/contract consistency through `g.check(mode='p')`. Approval evidence is supplied in memory and persistence is stubbed for this test. It does not certify review, staging, production admission or authorization.
- `evidence/staging_test/result.json` verifies streamed archive/member hashes and rejects corruption. Shell and Python syntax checks pass. Actual Orchard staging bytes remain unverified here.
- The new tree loads the native tiny model, runs a finite H1 S2 routing forward/backward with all 32 frame carriers, and resolves all 372 R0 rooms. `evidence/cpu/fallback_final/run/s2.json` records that check. The native first optimizer-step admission passes for the reduced CPU fixture in `run/inputs/first_step_993.json`.

The exact four-rank h1_headsft first-batch reproduction cannot run here. The supplied archive does not contain its `first_batch/real_fixture_batch.sh`, `tests/test_trainer.py` or `tests/test_review.py`; the model/restore/frames named by `receipts/rfb.sh` are outside the allowed inputs. Torchrun’s local TCP rendezvous is also denied by the workspace. No remote model download or other network access was used to fill those gaps.

The supplied receipts remain evidence from their producer, not new measurements of this derived kit. `receipts/real_forced2/SUMMARY.json` reports a diagnostic step-2 forced run with two own camera rows on each of four ranks, no refusals and no nonfinite results. The 91-test suite receipt is supplied evidence; this packet does not claim to have rerun that missing suite.

**USR1 and the verified fallback**

`job.sh` ends with `exec /bin/bash .../b/r.sh`, so the wrapper’s child becomes `r.sh` after initialization. `h.py`’s expected script/root pair matches the launch arguments. The relay deliberately signals rank processes rather than torchrun.

The code exposes a failure path: `i.py` reads descendant `/proc/<pid>/environ` without catching `PermissionError`; `h.py` also omits that exception while traversing processes. Such an error can abort the relay/supervisor. Meanwhile, the host `o/<job>.stop` marker is neither the namespace’s writable `o/` directory nor a condition polled by the training loop. Writing it does not itself stop training. The supplied incident has no traceback or process snapshot, so the exact failing PID and exception on D0 remain unconfirmed.

The patch catches permission failures and writes `stop.<job>.request` in the run directory, which `c.sh` binds into every rank. The trainer polls this file before training and after each optimizer update; the existing MAX reduction then selects the common checkpoint/export path. Job-specific filenames avoid stale-stop requests on same-node resume. The bridge does not require `/proc/environ`, torchrun signal forwarding or an environment variable from the host.

`evidence/stop_bridge/result.json` reproduces the old uncaught exception, verifies the patched relay, executes the exact new `on_stop` function and reads its marker through a real bwrap user namespace. A complete `jb.sh → job.sh → r.sh → i.py → torchrun → bwrap/ranks` proof is **not established**: the CPU chain failed before rank startup because TCPStore sockets were denied. The failed test exited; no cluster-killed job was relaunched.

The required alternate proof **passes**. `evidence/cpu/fallback_final/result.json` records a native tiny-model run with real optimizer updates, checkpoint serialization and milestone exports. It runs all 200 optimizer steps with the 1,000-step LR horizon, exports m100 and m200, returns `H1_STOP` / `h1_stop_after_step`, and sets `stopped_for_resume=false`. The loop takes {proof['run']['elapsed_seconds']:.2f} seconds on CPU. Its one-rank collectives and FSDP state gathering are local stand-ins; the model state, checkpoint payloads, hashes, export files and slot verification are real. The fixture uses reduced pose batches, not the production four-stream population or S1 own-row frequency.

The unchanged wrapper launch/wait/slot-copy suffix runs after the CPU job returns 0. It publishes a verified step-200 slot of **{proof['slot']['bytes']:,} bytes**, archive SHA256 `{proof['slot']['archive_sha256']}`. Its reread checks every payload against the native checkpoint manifest and binding. This proves the step limit and local slot publication, not distributed GPU behavior or GCS delivery. The code path is `run_steps`: `h1_limit` → `h1_stop` → `stopping` → `checkpoint` → `export` → break → `stopped_for_resume=false`.

The 13-hour budget is 28,000 seconds of training at 140 s/step, 7,200 seconds for admission (D0’s card reports about 1h45m), 3,600 seconds for staging, and 3,600 seconds for two exports plus slot persistence: 42,400 seconds, rounded to 46,800. Slurm sends USR1 at 43,200 seconds. These are planning allowances, not measured H1 wall times. The sealed recipe retains its 86,400-second budget because other recipe fields are not admitted overrides; the 200-step limit and Slurm signal provide the shorter allocation boundary.

**Operator procedure, in order**

1. Review this report, `DIFF.md`, `ids.json`, the CPU evidence and the new source members. Confirm no concurrent four-GPU advanced allocation conflicts. Confirm the new kit, bundle and persistent root do not exist on Orchard. The scripts refuse existing targets; they do not overwrite D0 or retry a failed deployment.
2. Run local `sha256sum -c SHA256SUMS.txt`. Carry `orch_h1.sh` through the existing authorized Orchard wrapper as the script body. It decodes its embedded archive into `{bun}`, verifies its digest and file checksums, and invokes `o.sh`. Alternatively, upload `build/{up['archive']}` as one file through that wrapper, verify its SHA256, extract only into the new bundle, and run `bash o.sh`. No transport or session capability is included in this packet.
3. `o.sh` derives a complete BLOCKED candidate in `BUN/p` from `x_07ca49df`; runs exact empty-override reproduction in `BUN/e`; and verifies identity/contract. It checks all inherited tar/extra part paths exist and hashes the changed extras and every new archive member, including the shared m544 archive. Its staging record distinguishes inherited availability/evidence from fresh byte checks. Native `c.sh` still rechecks staged inputs in the job. `archive.json` attests the uploaded trainer tar only after a hash readback on project storage.
4. Run the faithful gate on the login node before final derivation. The source command is:

   ```sh
   nice -19 python -B rows/faithful_gate.py <routing receipt> --out gate.json
   ```

   In the opaque deployment, set `PY_GATE` to an installed CPU interpreter with the pinned trainer dependencies, then run `bash {bun}/g.sh`. Set `BW_GATE` if bwrap has a nonstandard location. `g.sh` runs the same gate as `f.py`, extracts the routing archive into the new bundle, verifies the unchanged receipt and SQLite pins, and binds their logical paths read-only into a private bwrap namespace. It does not rewrite the receipt. Exit **0** permits the remaining launch checks; **1** stops H1 and returns the D0-allocation decision to the orchestrator; **2** is an input/runtime blocker. Keep `gate.json`, including identity rate, counts and refusal histogram. Native preparation repeats the gate on its bound receipt.
5. Obtain an independent PASS review in `BUN/review.json`, bound to the identity, source revision and admission contract above. Retain `admission_scope="pinned-template-and-native-data-derivation"`; name the actual reviewer and evidence. Do not promote the supplied PENDING draft merely because local fixtures pass. Verify `staging.json`, `archive.json` and the unchanged conditional `4.json`; its authorization expires 2026-11-26T00:00:00Z.
6. Run `bash {bun}/z.sh derive` (or `fin_h1.sh derive` through the wrapper). This derives the final kit from the sealed source, checks the final manifest against a fresh expected derivation with the explicit READY transition, and emits `compare.json`, `result.json`, `ready.json` and `anon.json`. Both formerly absent local payload entries must retain their sealed hashes. The draft config key is not used as a final staging attestation.
7. Perform the independent content scan on the exact final kit and every listed external file, including trainer tar members. The local pre-scan found **383 new identifying matches**, 372 in the required R0 list and 11 in its validator. `anon.json` stays UNREVIEWED until that content is reviewed under the applicable naming policy. Inherited code/module/member paths are preserved; newly selected upload destinations and the job name are opaque. After a valid CLEAN certificate binds the actual final manifest and external hashes, run `bash {bun}/z.sh certify`; it installs the certificate and runs `b/a.py`.
8. The operator mints fresh sessions for the **44 exact names in `EXPORT_OBJECTS.txt`**, using the inspected `jobB/mint.py` procedure and a new private output file. Its interface is `mint.py OUT 8865619b {tok['run']} m1 m50 m100 m200 m400 m600 m800 m1000 mstop mstopB mstopC`. It requests create-only GCS sessions. Install the new map only at `{kh}/sess.json`, mode 0600. Do not reuse or inspect D0’s session map. Confirm freshness and lifetime close to launch without exposing capability URIs. This packet contains no sessions and executes no minting.
9. All 44 names are retained to preserve the wrapper’s exact precheck. `c.sh` could support the reduced 20 names (m100, m200 and three stop generations, four parts each), but this wrapper intentionally requires D0’s full set. Normal H1 execution uses only m100/m200; early exits can use the stop generations. Key presence and mode do not prove that sessions work.
10. Confirm free space: the wrapper retains D0’s conservative 3.8-TB node-local admission, and project needs the slot plus 20 GB. D0’s real slot estimate is about 113 GB. The inherited GCS fallback verifies size/MD5 and publishes `SLOT_TO_GCS` before exit 6; it requires the operator’s approved Orchard cloud environment. The local proof covers the ordinary project slot path only.
11. Obtain the separate explicit GO in `BUN/go.json`, using `go.template.json` and binding the final manifest, wrapper hash, identity and contract. Run `bash {bun}/s.sh` through the Orchard wrapper. It rechecks those bindings and `b/a.py`, then submits:

   ```sh
   TZ=UTC env -u TK_JOB_START sbatch -J a15_cot_ap{tok['job']} -o /dev/null \\
     -e {kh}/o/%j.err -A mt01 -p advanced -N1 --ntasks=1 \\
     --gres=gpu:4 -c 48 --mem=800G -t 13:00:00 \\
     --signal=B:USR1@3600 --no-requeue {bun}/jb.sh
   ```

12. Watch native full-population admission, the four-rank first-step gate, finite losses, H1 metrics and the 1–50 answer-difference rule. At completion, verify m100/m200 or the registered early-stop export, the terminal report, and slot verification. A nonzero wrapper status or `SLOT_MISSING`, `SLOT_FAILED`, `SLOT_SKIPPED` is not successful persistence. `SLOT_TO_GCS`/exit 6 means the slot is remote and needs a separately checked restore procedure. Return the receipts and gate result to the orchestrator; these scripts never touch D0’s end slot or resume it.

**Unverified before launch**

The full routing identity rate, real rows/model first batch under this exact kit, four-rank signal delivery, real staging throughput, complete source reproduction with both missing local payloads, independent source/content approval, final remote manifest, production sessions, native admission, GPU behavior and GCS fallback are unverified here. The packet supplies executable checks and fails closed while those gates remain pending.

## Self-review against R9–R12

| Finding | H1 packet treatment |
|---|---|
| R9 §1: exact config changes, receipt relocation, division/provenance closure | Exact-field test passes. D0 rows, selection, division waiver, m544 artifact, nine archive members and full-weight pins are retained. Only the receipt’s physical upload source moves; its bytes do not change. The new code has separate source binding. |
| R9 §1: unchanged gate/trainer assertion | Not inherited as an H1 claim. `DIFF.md` lists every code/runtime change; independent review must cover them. |
| R9 §2: modes p/t/u, resources, expiry, separate GO | Draft 4.json binds the new source/config/contract, world 4 and 13 hours; production_go_granted stays false. In-job preparation is still required before t/u. |
| R9 §2: fixture has stale authorization/review/staging | The H1 fixture installs its own 4/review/staging records; review/staging remain explicitly PENDING. |
| R9 §3: 44 names, 0600, vt before restore, single TK_JOB_START | Retained. `v.py` performs the new archive check before restore. No session usability is claimed. |
| R9 §4: six local identifying paths in carried overrides | All local closure inputs are copied to opaque `d_<hex>.json` files; the remote override contains no Trinity workspace paths. Local overrides remain local. Full content certification is pending. |
| R9 §5: uploaded receipt bytes and precise zero-write claim | Login checks hash the new receipt and changed payloads. Zero project writes describes only the verification reads, not upload, extraction, derivation or training. |
| R9 final: READY manifest, content certificate, native gates | Separate final derivation, expected-manifest comparison, certification and submission phases enforce those boundaries. |
| R10 A2.1: c.sh overwrites IN | No A2 stage-2 scripts are shipped. Login scripts use BUN; the wrapper retains its reviewed paths. |
| R10 A2.2 / R11 A2.1 / R12 deadlines: finalization and descendants | A2’s timed CPU stage is not carried. The batch allocation and GCS fallback deadline both use 46,800 seconds; the 200-step fallback is proved locally. A distributed stop deadline still needs Orchard evidence. |
| R10 A2.3 / R11 A2.2 / R12 nonfatal logging: publication and exit preservation | No A2 publication/summary chain is carried. Native admission failure blocks training; wrapper slot code retains trainer exit status. The local successful path returns 0 with a verified slot. |
| R10 A2.4 / R11 A2.3 / R12 anonymous output: free-form strings | No A2 helper or blacklist is carried. The new faithful gate and source content require their own content review; UNREVIEWED is retained. No inherited A2 CLEAN certificate is reused. |
| R10 A2.5 / R11 family accounting | A2’s family census is not part of this packet. H1 reports its specified own/GT/refused per-type counts and refusal histogram; real-population results remain pending. |
| R10 B.1 / R11 B.1: SLOT_TO_GCS hash and marker publication | The R11-reviewed checks remain intact. The only deadline change is 86,400 → 46,800. No cloud fallback execution is claimed. |
| R10 B.2 / R11 B.2: stale staging config key | Staging binds config identity and source revision; it does not claim the draft file key is final. |
| R10/R11: absent payload hashes, READY transition and stale fixture manifest | Missing payload manifest lines are preserved. Orchard repeats empty derivation and compares the final READY inventory after updating the expected launch hash. The local fixture hash is never installed as a READY certificate. |
| R10/R11: refreshed external hashes and scan | Finalization enumerates every carried file plus generated gate/staging/archive/override evidence with current hashes. Certification rechecks them. |
| R12: A2 confirmation, no new defects | Those reviewed A2 bytes are not reused. This packet’s new code is covered only by the explicitly listed local tests and remains subject to its own independent review. |

The writing follows the no-archaeology skill. References to D0’s stop incident and R9–R12 remain because the requested fault analysis and review mapping require them. They are evidence boundaries, not production approval.
'''
(H/'REPORT.md').write_text(report)
print('Report written',len(report.encode()))
