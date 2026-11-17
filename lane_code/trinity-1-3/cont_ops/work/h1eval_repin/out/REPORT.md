# H1 export-pin evaluator package

Package `bf94a7976a7e9` is built in `out/package/`. Its payload is 5,298,254 bytes, SHA256 `4a41299cbcc78a2c57a48b285f43bf19558f747a3584365c96b23e9c9184df3e`. `out/0.tgz` contains the same bytes. The package includes all eight requested files. `REPORT_R1.md` preserves the supplied report verbatim.

The package reads export hashes, exact sizes, the observed archive member directory, lineage, step, and preparation metadata pins from `a/export.json`. `a/1.json` authenticates that file by SHA256 and bytes. Metadata check, submit, and job admission verify it. Admission compares the three export declarations against it before staging; staging authenticates the actual file bytes. Preparation authenticates its three selected files before running the existing structural checks.

The logical root remains `/scratch/jjyeung/b01ec87a6f29b`. The new package lives at `/project/community/jjyeung/bf94a7976a7e9` and returns under `bf94a7976a7e9<job-id-as-eight-hex-digits>`. The pinned policy paths remain unchanged. Each allocation has a verified job-private `/tmp` mount and an exclusive `/tmp/a<job-id><package-token>` bootstrap directory. Bubblewrap maps that allocation's physical `sj` directory to the shared logical namespace. Different allocations cannot share the same job-private data path.

Project-disk archive staging remains the supported route. This is the smaller change: no in-job GCS integration or vendored stager changes. `fill_export.py` streams the four locally placed parts with Python tarfile, checks the whole stream against the `.done` object/bytes/hash, discovers the member directory, and computes file and part pins without a joined archive copy. It checks artifact/member hashes, weight hashes, and preparation compatibility, then emits the export pin file, a small metadata tar, and adapted camera-only inputs. `EXPORT_SCHEMA.md` documents the schema; `export_544.json` contains the production values; `export_TEMPLATE.json` refuses until filled.

H1-1's supplied prepared config and data receipt satisfy the production checks that can be evaluated without the missing preparation receipt and export:

| Check | Evidence |
|---|---|
| Data receipt schema/status | `s1-in-job-data-v1`, `PREPARED`. |
| Real/rehearsal/synthetic flags | `real_frames_verified=true`, `rehearsal=false`; absent `synthetic` passes the existing default-false check. |
| Prepared config authentication | File SHA256 `65519f6f6399428615da3439e203e95a49967c6a2c6a73deac724696be061de2` equals `data_receipt.config.sha256`. |
| Preparation binding | `data_receipt.preparation == config.preparation == binding.preparation`, including source path and SHA256 `247671798be1b91e6594d3ba2b49d8659e2435830092b63352f8645bf6402d1a`. |
| Frame layout | Prepared config says `duplicate`. |
| Base identity | Prepared config says `c202236235762e1c871ad0ccb60c8ee5ba337b9a`, matching the frozen base. |

The admission request's `config` references `1dd078da.json` / `9385cc71…`; it is not the prepared config. Passing that training request directly as the evaluator request would fail `data.config == req.config`. The package constructs the evaluator request from the selected prepared config and preserves its original source identity. This keeps the complete dictionary equality check. The run binding's `26a60a5c…` is a training config identity, not a file hash; only the real preparation receipt and export artifact can establish the required `receipt.config_sha256 == artifact.config_sha256` equality.

The real H1-1 preparation receipt is absent both from the supplied folder and its small `r.tar`. The m100 export is also absent. No observed structural mismatch requires weakening a check, so the package is built; live H1-1 admission remains unproved and cannot proceed until those files exist. The helper refuses missing preparation files before scanning the large export.

All original restore conditions remain intact: data status/schema/flags and config/preparation equality, receipt/artifact config identity, base identity, duplicate frame layout, geometry-online guard, authenticated original model/assets, full-weights schema and bfloat16 dtype, weight names, every weight hash/size, index membership, and depth overwrite proof. An AST test confirms every original conditional guard is unchanged. The original-asset and depth-proof functions are unchanged. The additional checks authenticate the selected preparation files and their byte counts. The existing `step544_weights` provenance key remains for compatibility; its values are the selected export's verified weights.

The build uses the production `orchard_h10.build.build()` and its vendored `tar_bytes()` implementation: sorted USTAR members, existing modes, gzip level 6, and mtime 0. `build_package.py` points that builder at the authoritative extracted production inventory, adds the one new module, and supplies local builder/vendor locations. It does not refresh upstream reader code. The production archive, not the lagging supplied source snapshot, supplies unchanged bytes. The exact build and audit commands, run from this workspace, are:

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -B out/build_package.py
/scratch/jjyeung/envs/p1cpu/bin/python -B out/audit_package.py
```

The supplied builder snapshot differs from production in `job.py`, `operator.py`, and `runner.py`. `KIT_COMPARISON.json` and `SOURCE_COMPARISON.md` contain the inventory and complete input-source diffs. The supplied and production export stagers differ as modules; their `parse_done` and `stage_export` functions match exactly. Neither stager was modified.

`FILE_SHA256_DIFF.tsv` and `.json` prove all 915 unchanged payload members byte-identical against production `0.tgz` SHA256 `446a432306b8e68ebfa32228071259a61ffd2ec0dada3ec43a664ba342ca540e`. Nine existing members change and one is added. `DIFF.md` gives every changed file, line range, and reason; `package.patch` and `public.patch` contain every literal changed text line, including generated descriptors. `PLAN_DIFF.json` identifies every changed field of the generated one-line plan.

Scorers, statistics, items, perturbations, call cap, reader/e2e code, heads, tree, and all vendored SAM/selector/G3T/base/environment inventories remain byte-identical. Only `launch.py` changes within `h1eval`; only `stage_restore.py` changes within `parity_kit`. No non-export dependency or environment pin was regenerated.

Fourteen new-package tests and nine production-reference tests pass under the requested CPU interpreter, without dependency installation or fallback:

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -B out/tests/test_package.py
/scratch/jjyeung/envs/p1cpu/bin/python -B out/tests/test_constraints.py
```

`tests/results_r2.txt` and `tests/results_r1.txt` contain the results. Tests cover 544 admission; each artifact/heads/full-weights hash and size mismatch on either side of admission; missing, altered, or unsafe pins; actual preparation hash and size failures; original guard preservation; camera ordering; isolated physical mappings; sealed operator module loading; worker argument propagation; four-part receipt byte/hash/object/order failures; and complete helper output. Actual fixture launcher calls write journal bindings for SFT/544, SFT/100, and RL/37; the unchanged curve writer carries those labels through.

The 544-versus-H1-1 preparation mismatch test uses a clearly marked synthetic receipt with the supplied H1-1 config identity because the real receipt is unavailable. It proves the identity guard refuses that mismatch. It does not prove that the absent real H1-1 receipt has the claimed content or that a real export restores. Metadata tests stop before original-asset loading; no GPU weights, real parity run, or scoring accuracy are simulated as a pass. Operator/build helpers also pass syntax checks. `submerge.py` is byte-identical to the supplied complete-camera script, SHA256 `7abc0f94d5e93f57f823c78f5dfc6d3faf99eae87afab046b3c214f412b9aabe`.

Offline identities are recorded in `AUDIT.json`; the production reference values remain in `AUDIT_R1.json`:

| Identity | Result |
|---|---|
| Production plan | Reproduced `c6135410e087916095256a8b4c27eaa290f854734f8f4ea37150d34208ce709f`. |
| Production raw inputs | Reproduced `1abaf6ca0ebcf7a710292b5d337a59534a5a7ed178c48965a5530da5f9fd041f`. |
| New plan | `8f1b0de81bf2ce9f20783a7c20573d64ac2bf9ed3fa12929cc79cb1704a58d57`; changes with token and source pins. |
| Adapted 544 raw inputs | `93468153b4b4fc781fad664053281f3e92e80e3322eaaf76634f212e45b7c647` in `inputs_544.json`; changes because it adds the authenticated export-file reference. |
| Adapted 544 canonical inputs excluding resume | `d6a01e4459812c64c1d770112543969e3ce02ef75398c3169420ccd2158e3240`. |
| Item set | Unchanged `7162af725a9ee3e25e6054ee7d0cffc210c99d10ad8b097c6d3fb5b3319f7910`. |
| Reader code | Unchanged `2c2dc559f9ba529ec470be058528f7c12cf4c838f21df829a9c8ba5369d4b3af`. |
| Parity code | `a279de2ca5f54ea5ef13e27db3135b05f9773b63338d3590f224d57c45bb96c5`; changes because the authorized restore implementation changes. Production `64474315cfaf1bd3bdaf2171b20fd7c1d82ff065ca5db107bfccf5862f289bc3` is reproduced separately. |
| Evaluator code | `62d3fc991dd7f58257ea65653e6643eac5823a5e539543e9c7a57846637eb6c3`; changes because launcher labels now come from the pin file. Production `9fb4329d459aff71f0b42e615604437c09580adfb251550eef5dc70bfb33207d` is reproduced separately. |

Other legitimate changes include payload/public/package hashes, batch bootstrap, return token, preparation/settings/manifest/binding hashes, and the restored-export digest. The selected preparation files move to pinned paths under the data root; `RESTORE.json` records those paths and uses a generic export description. The manifest authenticates the changed evaluator and parity code. These changes are not scorer changes.

The camera return's export digest `46029ca2…` hashes the entire restored tree; its artifact-manifest binding digest is separately `0c41352a…`. Neither can be recomputed here without the absent weights and live restore. The new restored-tree digest is expected to differ because its authenticated provenance changes. The old camera evaluator was `ad9aeb95…`, which also differs from the supplied production archive's evaluator. The new read must be scored under this package's own evaluator hash; no old return is relabeled or reaccepted.

`OPERATIONS_DELTA.md` gives placement, four-part pull, pin filling, metadata check, an empty-root CPU check in the real node environment, one-GPU/four-hour submission on general, fetch, and scoring with the unchanged `submerge.py` and complete three-type prefix. The statistics remain room bootstrap, 10,000 draws, seed 20261115. The runbook verifies typed H100 resources before using the unchanged generic GPU submit helper and checks returned card evidence. If general is mixed or its GRES names omit GPU types, H100 placement is unproved and the operator must stop; no model-specific placement option was added outside the authorized scope.

No network, SSH, Slurm, GPU, or Git operation ran. No file was deleted. One erroneous deletion patch targeted a nonexistent `/tmp/nonexistent-placeholder` and failed without changing the filesystem. All successful new writes are under `out/`. Full Orchard staging/restore, H1-1 artifact compatibility, GPU inference, and complete-camera scoring still require the operator commands and actual inputs; no live pass or submission receipt is claimed.
