Run `out/arm_launch.sh` only with n_review1g's independent full task-A RESULT after the second discovery. The RESULT must contain the word PASS, the complete selection-file hash beginning `a49f117f`, and the complete generated-database hash beginning `5e35c3ce`. The helper authenticates compact receipt digest `522a3be3` separately; that digest is not the `--reviewed-regenerated-sha256` argument. No synthetic verdict or prepared test kit authorizes a launch.

```bash
nice -n 10 /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z11/out/arm_launch.sh /absolute/path/to/n_review1g_task_A_RESULT.txt 6000
```

Replace the RESULT path with the actual review file and use the measured, reviewed stop window. `3600` preserves the supplied constant. Other values must be ASCII integers, multiples of 300, in [3600,10800], exactly as `set_stop.py` requires. The runner invokes the unchanged setter on private copies for a nondefault value. This tool does not establish that either tested stop window meets the checkpoint/export budget in `out/ENOSPC_24M4Z10.md`.

The runner reads the actual `routing_selection.json`, `receipt.json` and `db_bytes.json` from `/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/d173912/173912/`. It checks their exact byte hashes, authenticates the selected base receipt in `work/build24m4m/inputs/ca0616dbc67cf9a257774b43a9d5b134957b3f3ce0451e6bf5378f3d7d0c1984`, and passes the reviewed hashes extracted from the RESULT into `arm_routing.apply`. The file hashes are pinned in `out/arm_launch.py`; receipt file `38c52f00` binds generated database `5e35c3ce`, while the base receipt binds input database `4e8e6c04`. The real RESULT remains an external input and is never synthesized by the runner.

The source kits are local `work/build24/kits/q` (reviewed q `df93cfba`), `out/kit_n` (`fb5c7f62`), and `out/kit_n_go` (`5c8ba4b4`). The recorded current overlay is `work/build24m4z11/OVERLAY_FILES.json` and `OVERLAY_SEALS.json`, authenticated against w24y2's actual q/n/n_go files. Its seals are q `df93cfba`, n `797255ae`, n_go `aa2d1267`. The frozen source tree and the supplied isolated Python environment must remain available locally; the delivery archive intentionally excludes the canonical trees.

Each invocation creates a fresh private `J/a_<random>/`. Its final `SUMMARY.json` and stdout identify the output directory, three seals, decoded n_go config hash, stop value and measured time. Successful offline preparation took 52.2 s at 3600 and 53.2 s at 6000 on trinity-1-18. Allow roughly 2 minutes for local preparation; no upload or service timing was measured.

Upload only the rows from the new run, with the target held throughout:

1. Confirm the current q/n overlay seals and the existing pool dependencies. The unchanged helper requires input DB `u/4e8e6c04…` (837,255,168 bytes) already staged. `db_bytes.json` reports its `pool_copy` as null, so these local checks do not prove that remote object exists. Resolve that prerequisite through the lane's authorized staging process before launch. The generated DB is 849,543,168 bytes. Neither database enters either small-file upload stream.
2. Apply that run's `UPLOADS_ARMED.json` / `.list` to X in listed order. Rows provide exact local paths, destination-relative names, SHA256, bytes, modes and expected baseline hashes. They carry the ordinary q/n delta and `u/a49f117f…`; verify/reuse the selection object if the discovery already installed it. Payloads precede each kit's `SHA256SUMS.txt`, then `BUILD.json`. Verify completed q/n seals before proceeding.
3. Apply `UPLOADS_ARMED_GO.json` / `.list` separately to X/n_go, in listed order, against the recorded n_go overlay. It contains only `n_go/` rows and requires the ordinary stream first. Verify its final seal and decoded `k/c.json` hash. Do not mix this stream into the ordinary upload.
4. Hand the verified armed n_go to the existing lane launch procedure after its remaining review/stop-window conditions hold. This runner performs no network operation, upload, scheduler call or launch.

The helper creates GO=false kits along its unchanged code path. After it succeeds, the wrapper restores n_go's exact authenticated source `k/a.json` bytes and its source BUILD GO field, reseals, and runs the decoded scan again. q and n retain GO=false; n_go retains the kit-defined GO=true admission capsule. The final manifests and final stdout supersede only the intermediate helper manifest inside `armed/`; upload from `UPLOADS_ARMED*` at the run root.

| Stop seconds | Kit | Final seal |
|---|---|---|
| 3600 | n | `2a8d73d342c958400c6a3202118e2e6a3b51066d19b2f01d627d4c992f91aeaa` |
| 3600 | n_go | `be082e270a5b258ef9c54d2342753aa082ebf334e01d0c7dfaa35f3d208ea043` |
| 3600 | q | `ece78fea6daa3acbee2a8571c1084097bcf780b0ad11a39e51752daeabf3b009` |
| 6000 | n | `a9eed3f47e8652a1e96e031a2298ab715b59f506deb4cc07609c8c3d9205fc30` |
| 6000 | n_go | `aeb1f9536c7de6bd2966eda2fb9b148abdf9544489d460de2886e71740b7e1c1` |
| 6000 | q | `ece78fea6daa3acbee2a8571c1084097bcf780b0ad11a39e51752daeabf3b009` |

The decoded-payload hash of final n_go `k/c.json` is `6d6fda1bedcb6ea2e9961b887d18f472a428975039ac962585d5b0b0365fbf90` at both tested stop values. Its capsule-file hash is `a1fd8b40387a1b5028004a1f232aea5e712a9f3dd8e3f8ba73b661cef24953d9`. `FULL_3600.json` and `FULL_6000.json` retain both hashes and all seals.

| Stop seconds | Compared kit | Actual changed members |
|---|---|---|
| 3600 | n | `BUILD.json`, `SHA256SUMS.txt`, `k/h.json`, `k/p.json`, `k/r.json` |
| 3600 | n_go | `BUILD.json`, `SHA256SUMS.txt`, `k/h.json`, `k/p.json`, `k/r.json` |
| 3600 | q | `BUILD.json`, `SHA256SUMS.txt`, `k/h.json`, `k/p.json`, `k/r.json` |
| 6000 | n | `BUILD.json`, `SHA256SUMS.txt`, `k/h.json`, `k/n.json`, `k/p.json`, `k/r.json` |
| 6000 | n_go | `BUILD.json`, `SHA256SUMS.txt`, `k/h.json`, `k/n.json`, `k/p.json`, `k/r.json` |
| 6000 | q | `BUILD.json`, `SHA256SUMS.txt`, `k/h.json`, `k/p.json`, `k/r.json` |

These comparisons cover every member, mode and byte hash, including an exact file-set check. n/n_go compare against the final upload kits; q compares against reviewed q. The 6000 run changes `k/n.json` only in n/n_go. `overlay_replay` independently applies both manifests to the actual current overlay inventories and requires complete final inventories, including modes. No source kit, qd, rcj or canonical tree changed.

| Test | Result | Evidence |
|---|---|---|
| full_3600 | OK | `work/build24m4z11/full_3600.log` |
| full_6000 | OK | `work/build24m4z11/full_6000.log` |
| missing_verdict | OK | `work/build24m4z11/missing_verdict.log` |
| without_pass | OK | `work/build24m4z11/without_pass.log` |
| wrong_selection | OK | `work/build24m4z11/wrong_selection.log` |
| wrong_regenerated | OK | `work/build24m4z11/wrong_regenerated.log` |
| altered_receipt | OK | `work/build24m4z11/altered_receipt.log` |
| altered_db_bytes | OK | `work/build24m4z11/altered_db_bytes.log` |
| invalid_stop_0 | OK | `work/build24m4z11/invalid_stop_0.log` |
| invalid_stop_1 | OK | `work/build24m4z11/invalid_stop_1.log` |
| invalid_stop_2 | OK | `work/build24m4z11/invalid_stop_2.log` |
| invalid_stop_3 | OK | `work/build24m4z11/invalid_stop_3.log` |
| invalid_stop_4 | OK | `work/build24m4z11/invalid_stop_4.log` |
| invalid_stop_5 | OK | `work/build24m4z11/invalid_stop_5.log` |
| native_wrong_selection | OK | `work/build24m4z11/native_wrong_selection.log` |
| native_wrong_regenerated | OK | `work/build24m4z11/native_wrong_regenerated.log` |
| native_altered_receipt | OK | `work/build24m4z11/native_altered_receipt.log` |
| native_altered_db_bytes | OK | `work/build24m4z11/native_altered_db_bytes.log` |
| overlay_replay | OK | `work/build24m4z11/TEST_RESULTS.json` |
| planner_selection_pin | OK | `work/build24m4z11/TEST_RESULTS.json` |
| discovery_comparison | OK | `work/build24m4z11/TEST_RESULTS.json` |
| helper_code_path | OK | `work/build24m4z11/TEST_RESULTS.json` |
| protected_files | OK | `work/build24m4z11/TEST_RESULTS.json` |
| Scanner source/AST/shell mutations and unknown environment key | OK | `work/build24m4z11/EXTRA_TESTS.json`, `scanner_*.log` |
| Recipe, GO and delivered native kit checkers | OK | `work/build24m4z11/EXTRA_TESTS.json` |
| Verdict surface and shell/Python syntax | OK | `work/build24m4z11/FINAL_AUDIT.json` |

Run the reproducible test suite with `nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/build24m4z11/tests.py` under the same 8-thread / 14-GiB limits as the launch shell. The fixture writes its synthetic verdict only in a mode-0700 temporary directory under J and moves that directory, plus its output kits, to `attic/build24m4z11/` in a finally block. Test runs are not upload candidates. `TEST_RESULTS.json` records their final attic locations. Compressed complete manifests, planner-closure reports and scans remain in `work/build24m4z11/evidence_3600/` and `evidence_6000/`; these are offline evidence. The production-pair verdict audit covers raw text in out/ and work/. The inherited work/build24m4y2/before/timings.json is preserved losslessly as timings.json.gz, with its raw bytes in attic, because its text also satisfied the production verdict gate; INHERITED_VERDICT_SURFACE.json records the byte hash.

The planner checks execute each delivered `b/pl.py` in an isolated interpreter for q and n_go at both stop values. A private copied kit redirects only `k/p.json.n_root` to a private pool containing the real selection as its `u/` object, then reseals. The unchanged `selection_pin` authenticates `a49f117f` in all four calls. This is a pin test, not a full planner materialization or production population check.

Armed q's `k/h.json.routing_selection` equals qp_11386117's object exactly. The complete decoded comparison is `work/build24m4z11/DISCOVERY_DIFF.json`:

| Capsule | Other differing top-level fields |
|---|---|
| `k/a.json` | `claims`, `discovery`, `discovery_pin`, `resource_request` |
| `k/h.json` | None |
| `k/p.json` | `pin_paths`, `uploads` |
| `k/r.json` | `staged_pins` |

The routing-selection objects in both h and r match. Arming additionally stages input DB `4e8e6c04` in r and includes its bytes and opaque pool path in p; discovery relies on its preceding r preparation and adds only the selection. q uses its reviewed control metadata. qp alone contains claims="nothing", discovery=true, discovery_pin provenance, and a discovery resource_request (48 CPUs, one GPU, 800G, preempt, four hours, no requeue); these fields describe its discovery probe and are absent from armed q. The comparison file lists every other value difference rather than treating discovery's control capsule as launch authorization.

`work/build24m4z11/ARM_ROUTING.diff` is the complete helper diff. It changes only the optional `kit_layout` parameter/CLI flag, origin selection and baseline file/seal/label selection. Omitting the option preserves the checked-in defaults. The entire verdict/selection/receipt/database validation block remains byte-identical; the test also compares every remaining apply statement's AST after excluding the origin/baseline assignments and manifest construction.

The local scanners require exact-byte compatibility certificates for the supplied final copier. `SCANNER.diff` and `ENVIRONMENT.diff` show the changes: the inherited diagnostic identifier and its internal attribute are accepted only at exact locations under source hash `e6d7a861`; seven literal runtime environment values are allowed only for that exact file. The environment scanner recognizes its exact AST's file-open forwarding, fixed getattr reads and TimeoutExpired exception class. The final b/pc.sh shell certificate pins the entire source and enumerates its literal assignments. Changed bytes/AST, changed shell and unknown environment keys refuse. The helper's verdict checks and every kit byte remain unchanged by these scanner certificates. Scanner certificates reside within J; no code or certificate is loaded through the inherited external scanner-directory link.

`work/build24m4z11/FAILURES.json` retains resolved scanner/setup failures with their full output and log paths. The symlink-related rename attempt failed with EXDEV; no write through that external link succeeded. No cluster-killed job was rerun. The requested baseline comparisons and failure ledger are retained because they establish the acceptance evidence.

The package is `out/tree_rebuild_b24m4z11_<sha8>.tar` (xz-compressed tar) plus its `.sha256`, written last. It contains out/ and work/, excludes canonical trees, attic and previous packages, and verifies every archived member's bytes, mode and link before publishing the checksum. `work/build24m4z11/PACKAGE_CHECK.json` records the final digest and archive verification.

The complete helper patch follows:

```diff
--- arm_routing.py (default)
+++ arm_routing.py (layout option)
@@ -11,7 +11,7 @@
         raise ValueError("R1_REVIEW_HASH_INVALID")
     return value.lower()
 
-def apply(source,db_bytes,output,*,reviewed_selection_sha256,reviewed_regenerated_sha256,review_verdict,base_path=None,regenerated_receipt_path=None):
+def apply(source,db_bytes,output,*,reviewed_selection_sha256,reviewed_regenerated_sha256,review_verdict,base_path=None,regenerated_receipt_path=None,kit_layout=None):
     source=Path(source).resolve();db_bytes=Path(db_bytes).resolve();output=Path(output).resolve()
     if not output.is_relative_to(L) or output==L:raise ValueError("R1_ARM_OUTPUT_OUTSIDE_WORKSPACE")
     if output.exists():raise ValueError("R1_ARM_OUTPUT_EXISTS")
@@ -63,7 +63,11 @@
         output_sizes={r.get("size") for r in output_matches}
         if len(output_sizes)!=1 or any(type(n) is not int or n<=0 for n in output_sizes):raise ValueError("R1_DATABASE_METADATA_SIZE_INVALID")
         native["database_bytes"]=next(iter(output_sizes))
-    origins={"q":L/"work/build24/kits/q","n":L/"work/build24/kits/n","n_go":L/"out/kit_n_go"}
+    layout=J.load(kit_layout) if kit_layout is not None else {}
+    origins={n:Path(p).resolve() for n,p in layout.get("origins",{"q":L/"work/build24/kits/q","n":L/"work/build24/kits/n","n_go":L/"out/kit_n_go"}).items()}
+    baseline_files=Path(layout.get("baseline_files",D/"ARM_BASE_FILES.json"))
+    baseline_seals=Path(layout.get("baseline_seals",D/"ARM_BASE_SEALS.json"))
+    baseline_label=layout.get("baseline_label","Orchard q and n after UPLOADS_24M4M; exact recorded seals and file inventory")
     selected_base=value["inputs_pinned"].get("routing_base") or J.load(origins["q"]/"k/r.json")["routing_base"]
     bh=pin(selected_base,"R1_ROUTING_SELECTION_BASE_INVALID")
     base_path=Path(base_path).resolve() if base_path else D/"inputs"/bh
@@ -77,7 +81,7 @@
         for h,n in ((dh,size),(selection_hash,source.stat().st_size)):
             if h in uploads and uploads[h]["bytes"]!=n:raise ValueError("R1_STAGED_PIN_SIZE_DIFFERS:"+h)
     output.mkdir();destination=output/"kits";upload=output/"upload";upload.mkdir();destination.mkdir()
-    baseline=J.load(D/"ARM_BASE_FILES.json")
+    baseline=J.load(baseline_files)
     rows=[];seals={};checks={};mutated={"k/h.json","k/r.json","k/p.json","k/a.json","BUILD.json","SHA256SUMS.txt"}
     for name,origin in origins.items():
         target=destination/name
@@ -130,7 +134,7 @@
     config_hashes=dict(path=str(config_path),payload_sha256=config_payload_hash,file_sha256=J.sha(config_path))
     rows.append(dict(name="u/"+selection_hash,local_path=str(out),bytes=out.stat().st_size,sha256=selection_hash,mode="0644",action="add"))
     assert not (upload/"u"/dh).exists() and all(r["name"]!="u/"+dh for r in rows)
-    manifest=dict(schema="routing-armed-v3",baseline="Orchard q and n after UPLOADS_24M4M; exact recorded seals and file inventory", baseline_kit_seals={n:J.load(D/"ARM_BASE_SEALS.json")[n] for n in ("q","n")}, baseline_files={n:baseline[n] for n in ("q","n")},files=rows,
+    manifest=dict(schema="routing-armed-v3",baseline=baseline_label, baseline_kit_seals={n:J.load(baseline_seals)[n] for n in ("q","n")}, baseline_files={n:baseline[n] for n in ("q","n")},files=rows,
         total_files=len(rows),total_bytes=sum(r["bytes"] for r in rows),stream_root=str(upload),kits=seals,
         routing_selection_sha256=selection_hash,regenerated_sha256=value["regenerated_sha256"],
         review=dict(reviewed_selection_sha256=reviewed_selection_sha256,reviewed_regenerated_sha256=reviewed_regenerated_sha256,
@@ -155,9 +159,10 @@
     parser.add_argument("--reviewed-regenerated-sha256",required=True,type=reviewed_hash)
     parser.add_argument("--review-verdict",required=True,type=Path)
     parser.add_argument("--regenerated-receipt",type=Path,help="Published native receipt; required when the selection binds regenerated_receipt")
+    parser.add_argument("--kit-layout",type=Path,help="Origins and baseline inventory/seals; omitted preserves the default layout")
     args=parser.parse_args();v=apply(args.selection,args.db_bytes,args.output,base_path=args.routing_base,
         reviewed_selection_sha256=args.reviewed_selection_sha256,reviewed_regenerated_sha256=args.reviewed_regenerated_sha256,
-        review_verdict=args.review_verdict,regenerated_receipt_path=args.regenerated_receipt)
+        review_verdict=args.review_verdict,regenerated_receipt_path=args.regenerated_receipt,kit_layout=args.kit_layout)
     print(json.dumps(dict(kits=v["kits"],armed_n_go_config=v["armed_n_go_config"],files=v["total_files"],database=v["already_staged"],output=str(args.output),uploaded=False,launched=False)))
 
 if __name__=="__main__":main()
```
