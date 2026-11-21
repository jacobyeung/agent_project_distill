from pathlib import Path
import json
L=Path(__file__).resolve().parents[2];D=L/'work/build24m4z11';O=L/'out'
r=json.loads((D/'TEST_RESULTS.json').read_text());assert r['status']=='OK'
full=[json.loads((D/('FULL_'+str(s)+'.json')).read_text()) for s in (3600,6000)]
diff=json.loads((D/'DISCOVERY_DIFF.json').read_text())
rows='\n'.join('| '+t['case']+' | OK | `work/build24m4z11/'+(t['case']+'.log' if (D/(t['case']+'.log')).exists() else 'TEST_RESULTS.json')+'` |' for t in r['tests'])
seals='\n'.join('| '+str(v['stop_before_seconds'])+' | '+n+' | `'+h+'` |' for v in full for n,h in v['kits'].items())
changes='\n'.join('| '+str(v['stop_before_seconds'])+' | '+n+' | '+', '.join('`'+p+'`' for p in paths)+' |' for v in full for n,paths in v['changes'].items())
keys='\n'.join('| `'+rel+'` | '+(', '.join('`'+k+'`' for k in fields) or 'None')+' |' for rel,fields in diff.items())
text=f'''Run `out/arm_launch.sh` only with n_review1g's independent full task-A RESULT after the second discovery. The RESULT must contain the word PASS, the complete selection-file hash beginning `a49f117f`, and the complete generated-database hash beginning `5e35c3ce`. The helper authenticates compact receipt digest `522a3be3` separately; that digest is not the `--reviewed-regenerated-sha256` argument. No synthetic verdict or prepared test kit authorizes a launch.

```bash
nice -n 10 /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z11/out/arm_launch.sh /absolute/path/to/n_review1g_task_A_RESULT.txt 6000
```

Replace the RESULT path with the actual review file and use the measured, reviewed stop window. `3600` preserves the supplied constant. Other values must be ASCII integers, multiples of 300, in [3600,10800], exactly as `set_stop.py` requires. The runner invokes the unchanged setter on private copies for a nondefault value. This tool does not establish that either tested stop window meets the checkpoint/export budget in `out/ENOSPC_24M4Z10.md`.

The runner reads the actual `routing_selection.json`, `receipt.json` and `db_bytes.json` from `/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/d173912/173912/`. It checks their exact byte hashes, authenticates the selected base receipt in `work/build24m4m/inputs/ca0616dbc67cf9a257774b43a9d5b134957b3f3ce0451e6bf5378f3d7d0c1984`, and passes the reviewed hashes extracted from the RESULT into `arm_routing.apply`. The file hashes are pinned in `out/arm_launch.py`; receipt file `38c52f00` binds generated database `5e35c3ce`, while the base receipt binds input database `4e8e6c04`. The real RESULT remains an external input and is never synthesized by the runner.

The source kits are local `work/build24/kits/q` (reviewed q `df93cfba`), `out/kit_n` (`fb5c7f62`), and `out/kit_n_go` (`5c8ba4b4`). The recorded current overlay is `work/build24m4z11/OVERLAY_FILES.json` and `OVERLAY_SEALS.json`, authenticated against w24y2's actual q/n/n_go files. Its seals are q `df93cfba`, n `797255ae`, n_go `aa2d1267`. The frozen source tree and the supplied isolated Python environment must remain available locally; the delivery archive intentionally excludes the canonical trees.

Each invocation creates a fresh private `J/a_<random>/`. Its final `SUMMARY.json` and stdout identify the output directory, three seals, decoded n_go config hash, stop value and measured time. Successful offline preparation took {full[0]['seconds']:.1f} s at 3600 and {full[1]['seconds']:.1f} s at 6000 on trinity-1-18. Allow roughly {max(1,round(max(v['seconds'] for v in full)/60+1))} minutes for local preparation; no upload or service timing was measured.

Upload only the rows from the new run, with the target held throughout:

1. Confirm the current q/n overlay seals and the existing pool dependencies. The unchanged helper requires input DB `u/4e8e6c04…` (837,255,168 bytes) already staged. `db_bytes.json` reports its `pool_copy` as null, so these local checks do not prove that remote object exists. Resolve that prerequisite through the lane's authorized staging process before launch. The generated DB is 849,543,168 bytes. Neither database enters either small-file upload stream.
2. Apply that run's `UPLOADS_ARMED.json` / `.list` to X in listed order. Rows provide exact local paths, destination-relative names, SHA256, bytes, modes and expected baseline hashes. They carry the ordinary q/n delta and `u/a49f117f…`; verify/reuse the selection object if the discovery already installed it. Payloads precede each kit's `SHA256SUMS.txt`, then `BUILD.json`. Verify completed q/n seals before proceeding.
3. Apply `UPLOADS_ARMED_GO.json` / `.list` separately to X/n_go, in listed order, against the recorded n_go overlay. It contains only `n_go/` rows and requires the ordinary stream first. Verify its final seal and decoded `k/c.json` hash. Do not mix this stream into the ordinary upload.
4. Hand the verified armed n_go to the existing lane launch procedure after its remaining review/stop-window conditions hold. This runner performs no network operation, upload, scheduler call or launch.

The helper creates GO=false kits along its unchanged code path. After it succeeds, the wrapper restores n_go's exact authenticated source `k/a.json` bytes and its source BUILD GO field, reseals, and runs the decoded scan again. q and n retain GO=false; n_go retains the kit-defined GO=true admission capsule. The final manifests and final stdout supersede only the intermediate helper manifest inside `armed/`; upload from `UPLOADS_ARMED*` at the run root.

| Stop seconds | Kit | Final seal |
|---|---|---|
{seals}

The decoded-payload hash of final n_go `k/c.json` is `{full[0]['armed_n_go_config']['payload_sha256']}` at both tested stop values. Its capsule-file hash is `{full[0]['armed_n_go_config']['file_sha256']}`. `FULL_3600.json` and `FULL_6000.json` retain both hashes and all seals.

| Stop seconds | Compared kit | Actual changed members |
|---|---|---|
{changes}

These comparisons cover every member, mode and byte hash, including an exact file-set check. n/n_go compare against the final upload kits; q compares against reviewed q. The 6000 run changes `k/n.json` only in n/n_go. `overlay_replay` independently applies both manifests to the actual current overlay inventories and requires complete final inventories, including modes. No source kit, qd, rcj or canonical tree changed.

| Test | Result | Evidence |
|---|---|---|
{rows}
| Scanner source/AST/shell mutations and unknown environment key | OK | `work/build24m4z11/EXTRA_TESTS.json`, `scanner_*.log` |
| Recipe, GO and delivered native kit checkers | OK | `work/build24m4z11/EXTRA_TESTS.json` |
| Verdict surface and shell/Python syntax | OK | `work/build24m4z11/FINAL_AUDIT.json` |

Run the reproducible test suite with `nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/build24m4z11/tests.py` under the same 8-thread / 14-GiB limits as the launch shell. The fixture writes its synthetic verdict only in a mode-0700 temporary directory under J and moves that directory, plus its output kits, to `attic/build24m4z11/` in a finally block. Test runs are not upload candidates. `TEST_RESULTS.json` records their final attic locations. Compressed complete manifests, planner-closure reports and scans remain in `work/build24m4z11/evidence_3600/` and `evidence_6000/`; these are offline evidence. The production-pair verdict audit covers raw text in out/ and work/. The inherited work/build24m4y2/before/timings.json is preserved losslessly as timings.json.gz, with its raw bytes in attic, because its text also satisfied the production verdict gate; INHERITED_VERDICT_SURFACE.json records the byte hash.

The planner checks execute each delivered `b/pl.py` in an isolated interpreter for q and n_go at both stop values. A private copied kit redirects only `k/p.json.n_root` to a private pool containing the real selection as its `u/` object, then reseals. The unchanged `selection_pin` authenticates `a49f117f` in all four calls. This is a pin test, not a full planner materialization or production population check.

Armed q's `k/h.json.routing_selection` equals qp_11386117's object exactly. The complete decoded comparison is `work/build24m4z11/DISCOVERY_DIFF.json`:

| Capsule | Other differing top-level fields |
|---|---|
{keys}

The routing-selection objects in both h and r match. Arming additionally stages input DB `4e8e6c04` in r and includes its bytes and opaque pool path in p; discovery relies on its preceding r preparation and adds only the selection. q uses its reviewed control metadata. qp alone contains claims="nothing", discovery=true, discovery_pin provenance, and a discovery resource_request (48 CPUs, one GPU, 800G, preempt, four hours, no requeue); these fields describe its discovery probe and are absent from armed q. The comparison file lists every other value difference rather than treating discovery's control capsule as launch authorization.

`work/build24m4z11/ARM_ROUTING.diff` is the complete helper diff. It changes only the optional `kit_layout` parameter/CLI flag, origin selection and baseline file/seal/label selection. Omitting the option preserves the checked-in defaults. The entire verdict/selection/receipt/database validation block remains byte-identical; the test also compares every remaining apply statement's AST after excluding the origin/baseline assignments and manifest construction.

The local scanners require exact-byte compatibility certificates for the supplied final copier. `SCANNER.diff` and `ENVIRONMENT.diff` show the changes: the inherited diagnostic identifier and its internal attribute are accepted only at exact locations under source hash `e6d7a861`; seven literal runtime environment values are allowed only for that exact file. The environment scanner recognizes its exact AST's file-open forwarding, fixed getattr reads and TimeoutExpired exception class. The final b/pc.sh shell certificate pins the entire source and enumerates its literal assignments. Changed bytes/AST, changed shell and unknown environment keys refuse. The helper's verdict checks and every kit byte remain unchanged by these scanner certificates. Scanner certificates reside within J; no code or certificate is loaded through the inherited external scanner-directory link.

`work/build24m4z11/FAILURES.json` retains resolved scanner/setup failures with their full output and log paths. The symlink-related rename attempt failed with EXDEV; no write through that external link succeeded. No cluster-killed job was rerun. The requested baseline comparisons and failure ledger are retained because they establish the acceptance evidence.

The package is `out/tree_rebuild_b24m4z11_<sha8>.tar` (xz-compressed tar) plus its `.sha256`, written last. It contains out/ and work/, excludes canonical trees, attic and previous packages, and verifies every archived member's bytes, mode and link before publishing the checksum. `work/build24m4z11/PACKAGE_CHECK.json` records the final digest and archive verification.
'''
text+='\nThe complete helper patch follows:\n\n```diff\n'+(D/'ARM_ROUTING.diff').read_text()+'```\n'
(O/'ARM_LAUNCH_24M4Z11.md').write_text(text)
(O/'BUILD24M4Z11_REPORT.md').write_text('''The launch runner prepares final q/n/n_go copies from the independent task-A verdict; it performs no upload or launch.
The helper diff touches only origin/baseline selection; its verdict and evidence-validation block is byte-identical.
Both stop values (3600, 6000), six required refusals, native refusals, planner pins and complete overlay replay succeeded offline.
The ordinary stream excludes n_go; the GO stream is separate and preserves its authenticated GO capsule.
All canonical trees, qd, rcj and supplied kits retain their bytes and modes; synthetic verdicts and test kits reside in attic.
Exact-source scanner certificates support the supplied copier; mutation negatives refuse. Full failure output is retained.
Usage, seals, payload hash, differences and staging prerequisites: out/ARM_LAUNCH_24M4Z11.md.
Evidence: work/build24m4z11/{TEST_RESULTS,EXTRA_TESTS,FINAL_AUDIT,PACKAGE_CHECK}.json; package checksum is written last.
''')
print('Wrote usage and 8-line report')
