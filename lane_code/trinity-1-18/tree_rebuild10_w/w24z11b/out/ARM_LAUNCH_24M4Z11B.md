The launch runner uses the reviewed 24m4z12 upload kits. Run it only with n_review1g's independent full task-A RESULT after the second discovery. The RESULT must contain the word PASS and the full selection-file and generated-database hashes beginning `a49f117f` and `5e35c3ce`. The compact receipt digest `522a3be3` is checked separately. Synthetic test verdicts do not authorize a launch.

```bash
nice -n 10 /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z11b/out/arm_launch.sh /absolute/path/to/n_review1g_task_A_RESULT.txt 3600
```

Use the measured, reviewed stop window. The runner accepts ASCII integers that are multiples of 300 in [3600,10800]. At 3600 it preserves the supplied constant; other values use unchanged `set_stop.py` on private copies. These offline tests do not establish a safe checkpoint/export budget. The runner uses the supplied isolated Python, eight-thread limits, and a 14-GiB address-space limit.

Inputs are `routing_selection.json`, `receipt.json`, and `db_bytes.json` from `/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/d173912/173912/`, the real RESULT, and the bundled base receipt under `work/build24m4m/inputs/`. The runner checks the pinned file hashes before arming. The canonical trees and Python environment must remain available locally.

| Source kit | Full verified seal |
|---|---|
| `work/build24/kits/q` | `df93cfba9769ca82f48ac3bfdbb117ffc2d06b6f694ed1694c23d815fa97e2a9` |
| `out/kit_n` | `402a2fe23831c449e46cdb0b80fa9cde41e0bd5abf6d9edb57a106c0d5b202f2` |
| `out/kit_n_go` | `22db0727c2eb58c14cd14d371799b9e508264ab201155ec68243597bb9598444` |

The two N kits exactly match `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z12/out/`. `SOURCE_KITS.json` records all member hashes and modes. Their complete differences from 24m4z10 are:

| Kit | Changed members |
|---|---|
| n | `b/pc.py`, `BUILD.json`, `SHA256SUMS.txt` |
| n_go | `b/pc.py`, `BUILD.json`, `SHA256SUMS.txt` |

`work/build24m4z11b/n_pc.diff` and `n_go_pc.diff` contain the source comparisons. The old local kits are preserved in `attic/build24m4z11b/`.

Each invocation creates a private `J/a_<random>/` and reports its path, seals, config hashes, stop value, and elapsed time in stdout and `SUMMARY.json`. Offline preparation took 46.8 seconds at 3600 and 47.0 seconds at 6000. Allow approximately 2 minutes locally; no service timing was measured.

Hold the target while applying these steps:

1. Confirm the current overlay: q `df93cfba`, n `797255ae`, n_go `aa2d1267`. `work/build24m4z11b/OVERLAY_FILES.json` and `OVERLAY_SEALS.json` record its full inventory and seals, checked against the actual w24y2 kits by overlay replay.
2. Confirm the pool prerequisite `u/4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84`, **837,255,168 bytes**. The supplied metadata has `pool_copy=null`; local arming does not prove remote presence. The generated DB is 849,543,168 bytes. Neither database enters these small-file streams.
3. Upload only the fresh run's `UPLOADS_ARMED.json/.list`, in listed order: q/n payloads and selection `u/a49f117f…`, then `SHA256SUMS.txt`, then `BUILD.json`. Verify completed seals. Rows provide source paths, destination names, sizes, modes, hashes, and expected overlay hashes.
4. Apply that run's separate `UPLOADS_ARMED_GO.json/.list` to n_go after the ordinary stream, and verify its seal and decoded config hash. This stream contains only n_go rows. Hand the verified kit to the existing lane launch procedure after its review and stop-window conditions hold.

Use only fresh run-root manifests. Inherited upload manifests and reports are historical evidence. The helper's intermediate manifest under `armed/` is not the final upload stream. q/n retain GO=false; n_go retains its source GO=true capsule. The runner performs no upload or launch.

| Stop seconds | Kit | Final seal |
|---|---|---|
| 3600 | n | `f348f7a45d456412b629e724986feabbd6febadadec1946905cd3d24b1dc7b26` |
| 3600 | n_go | `3f55530cc3874ed3734f08c1e31589389ab8631ce9d0205b881e682b3e519b0c` |
| 3600 | q | `ece78fea6daa3acbee2a8571c1084097bcf780b0ad11a39e51752daeabf3b009` |
| 6000 | n | `f77cf8798376c2a3a08e09ec6409066693ad442978220bc7211e65a0df15a9b6` |
| 6000 | n_go | `5a24c3ece9376d1ceb20b7806947cdb44d602333ffd77feb1779d4a661928635` |
| 6000 | q | `ece78fea6daa3acbee2a8571c1084097bcf780b0ad11a39e51752daeabf3b009` |

The decoded n_go `k/c.json` payload SHA256 is `6d6fda1bedcb6ea2e9961b887d18f472a428975039ac962585d5b0b0365fbf90` at both stops. Its capsule-file SHA256 is `a1fd8b40387a1b5028004a1f232aea5e712a9f3dd8e3f8ba73b661cef24953d9`.

| Stop seconds | Kit compared with its source | Changed members |
|---|---|---|
| 3600 | n | `BUILD.json`, `SHA256SUMS.txt`, `k/h.json`, `k/p.json`, `k/r.json` |
| 3600 | n_go | `BUILD.json`, `SHA256SUMS.txt`, `k/h.json`, `k/p.json`, `k/r.json` |
| 3600 | q | `BUILD.json`, `SHA256SUMS.txt`, `k/h.json`, `k/p.json`, `k/r.json` |
| 6000 | n | `BUILD.json`, `SHA256SUMS.txt`, `k/h.json`, `k/n.json`, `k/p.json`, `k/r.json` |
| 6000 | n_go | `BUILD.json`, `SHA256SUMS.txt`, `k/h.json`, `k/n.json`, `k/p.json`, `k/r.json` |
| 6000 | q | `BUILD.json`, `SHA256SUMS.txt`, `k/h.json`, `k/p.json`, `k/r.json` |

The member comparisons include exact file sets, byte hashes, and modes. q compares with the reviewed q source; n/n_go compare with the delivered 24m4z12 kits. `k/a.json` remains byte-identical after final GO restoration. Only n/n_go change `k/n.json` at 6000. The canonical trees, qd, rcj, and source kits remain unchanged during testing.

| Test | Result | Evidence |
|---|---|---|
| full_3600 | OK | `work/build24m4z11b/full_3600.log` |
| full_6000 | OK | `work/build24m4z11b/full_6000.log` |
| missing_verdict | OK | `work/build24m4z11b/missing_verdict.log` |
| without_pass | OK | `work/build24m4z11b/without_pass.log` |
| wrong_selection | OK | `work/build24m4z11b/wrong_selection.log` |
| wrong_regenerated | OK | `work/build24m4z11b/wrong_regenerated.log` |
| altered_receipt | OK | `work/build24m4z11b/altered_receipt.log` |
| altered_db_bytes | OK | `work/build24m4z11b/altered_db_bytes.log` |
| invalid_stop_0 | OK | `work/build24m4z11b/invalid_stop_0.log` |
| invalid_stop_1 | OK | `work/build24m4z11b/invalid_stop_1.log` |
| invalid_stop_2 | OK | `work/build24m4z11b/invalid_stop_2.log` |
| invalid_stop_3 | OK | `work/build24m4z11b/invalid_stop_3.log` |
| invalid_stop_4 | OK | `work/build24m4z11b/invalid_stop_4.log` |
| invalid_stop_5 | OK | `work/build24m4z11b/invalid_stop_5.log` |
| native_wrong_selection | OK | `work/build24m4z11b/native_wrong_selection.log` |
| native_wrong_regenerated | OK | `work/build24m4z11b/native_wrong_regenerated.log` |
| native_altered_receipt | OK | `work/build24m4z11b/native_altered_receipt.log` |
| native_altered_db_bytes | OK | `work/build24m4z11b/native_altered_db_bytes.log` |
| overlay_replay | OK | `work/build24m4z11b/TEST_RESULTS.json` |
| planner_selection_pin | OK | `work/build24m4z11b/TEST_RESULTS.json` |
| discovery_comparison | OK | `work/build24m4z11b/TEST_RESULTS.json` |
| helper_code_path | OK | `work/build24m4z11b/TEST_RESULTS.json` |
| protected_files | OK | `work/build24m4z11b/TEST_RESULTS.json` |
| scanner_changed_program | OK | `work/build24m4z11b/EXTRA_TESTS.json` |
| scanner_changed_ast | OK | `work/build24m4z11b/EXTRA_TESTS.json` |
| scanner_unknown_environment | OK | `work/build24m4z11b/EXTRA_TESTS.json` |
| scanner_changed_shell | OK | `work/build24m4z11b/EXTRA_TESTS.json` |
| recipes_go_native_checkers | OK | `work/build24m4z11b/EXTRA_TESTS.json` |
| Verdict surface, source seals, shell/Python syntax | OK | `work/build24m4z11b/FINAL_AUDIT.json` |

The suite runs through `work/build24m4z11b/tests.py`, then `extra_tests.py`, then `final_audit.py`, using `nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B` under the launch shell's resource limits. Synthetic verdicts are created only inside mode-0700 private temporary directories under J and moved to attic afterward. `TEST_RESULTS.json` records their attic paths and the test output locations. Compressed manifests, planner closure reports, decoded scans, and complete final inventories are in `evidence_3600/` and `evidence_6000/`. No production-acceptable plaintext verdict remains in out/ or work/.

Planner `selection_pin` authenticates the real selection in q and n_go at both stops. Private test copies redirect only `n_root` to a private pool and reseal. This tests pin authentication, not full production materialization. Overlay replay checks the complete final inventory and modes after applying both streams.

Armed q's `k/h.json.routing_selection` equals discovery qp_11386117's object exactly. `DISCOVERY_DIFF.json` lists every decoded difference: h has none; r differs in `staged_pins`; p differs in `pin_paths` and `uploads`; a differs in `claims`, `discovery`, `discovery_pin`, and `resource_request`. Arming includes the input DB in the pool inventory; discovery relies on preceding preparation. The admission fields distinguish the reviewed q control from the discovery probe.

`arm_routing.py` is byte-identical to 24m4z11, SHA256 `3dbd7af286da10a14666d289ff75d9b056149ef3bf6fc5f98dbf66aa4ba7ee60`. Its verdict gate and validation code are unchanged. The tests also retain the original helper's byte/AST comparison. `arm_launch.py.diff` records only the source seals and evidence-directory change. Scanner diffs pin final `b/pc.py` source and AST hashes and exact diagnostic environment locations (173 and 537); shell certificates and allowed environment keys stay unchanged. Source, AST, shell, and unknown-key mutation tests all refuse.

`FAILURES.json` retains the full resolved scanner-location failure: `INPUT_NAME:b/pc.py:537:environment:TK_DIAGNOSTIC_PREFIX`. It was a normal test refusal, not a cluster-killed process. There are no unresolved failures.

The delivery is `out/tree_rebuild_b24m4z11b_<sha8>.tar` (xz-compressed tar) with `.sha256` written last. It contains out/ and work/, excludes canonical trees, attic, and earlier delivery packages, and verifies every archived member's bytes, mode, and link. `work/build24m4z11b/PACKAGE_CHECK.json` records the package verification and digest.
