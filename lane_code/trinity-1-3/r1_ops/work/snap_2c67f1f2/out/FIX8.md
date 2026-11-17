Proof 2 binds 747 of 747 supplied unit rows. All 747 packed rows pass sealed validation and native source selection; 0 rows are refused. The refusal list is `[]`. All supplied payload fields and source QIDs remain unchanged. The packer adds only events and frame inputs. All 23,904 frame pins resolve against the production-equal map, plan and FPS authorities. Actual RGB-byte validation remains pending.

Feet have 683 eligible rows. The feet-only cell is 1.00 row per step, with a 2.73 ceiling (273 cents; the exact repeat limit is 4 × 683 / 1,000 = 2.732). Inches are explicitly named missing at 64 eligible rows, below the 100-row threshold; cm is named missing at zero. The bound source retains the inches rows, but the allowlist samples feet only.

| Program cell after pro-rata refill | Rows/step |
|---|---:|
| Camera displacement | 18.25 |
| Camera movement direction | 15.88 |
| Camera rotation | 12.53 |
| Absolute distance | 16.34 |

The local frame-authority manifest is `FRAME_AUTHORITY.local.json`, SHA256 `a7ee3b6f3049bbf4827d0449328ada72f9aa34f317d7f411c1cb24bad06c7526`. `REBIND8.local.json` records the executed rebind argv with `--pack-unit-slice --units-allowlist ft --unit-cents 100`. `units/u.json` records all packing counts, refusals, authority pins and sealed implementation hashes. A missing requested frame refuses the row with its QID and every missing index; the test exercises that branch without inventing a pin.

The printed routing census uses g0–g3 and preserves the unknown-row check: more than 1% unknown eligible distance rows fails the audit. The local-only mapping is `CENSUS_CODES.local.json`, SHA256 `ce269588e21f0d62aa988a78a5026dc9e0601f4efeb645f342910ed6f759823c`. Every printed audit record encodes dataset-bearing keys recursively. The audit prints the mapping hash; the archive excludes the mapping file. Stored training payloads remain unchanged.

The namespace probe creates and tests `/home`, a path that names no user. Its source and captured argv contain no `/home/` literal. The probe retains its device, proc, user namespace, UID/GID and read-only home checks. The argv regression uses a stub; it does not claim local kernel namespace admission.

All 37 packet tests pass, including the real 747-row packing and native regeneration, exact payload and frame-pin comparisons, missing-frame refusal, printed opaque keys, mapping exclusion from the archive, namespace argv, and unknown-prefix threshold cases. `tools/run_local_checks.py` also checks deterministic packaging, two identical deployment fixtures, four-rank OFF identity, and the final-config first batch. Production preparation, actual RGB-byte admission and independent review remain pending.

Config identity: `2c67f1f25114ab1324cee10b796e86afc79d01999ad3881860ab35710e7fee5d`.
Run key: `78d0a06c`.
Archive: `p_6f8ed106.tar`.
Archive SHA256: `def1e1f2b1153328b024209e69fcbb71f2dd556b7376eacb836d40bb66d9845f`.

`FIX8.diff` compares tools, tests, configs, out, STATUS.md, the trainer tree and the proof parent against `/scratch/jjyeung/orch_n30/r1_ops/work/snap_d8b03fd1`. Binary changes include before/after hashes. The diff excludes itself, this note and SHA256SUMS to avoid recursion. The checksum manifest authenticates both FIX8 files. The frozen proof-1 archive remains `888027436a99cfec360959c46f4271222e4c029f5d36eb9870fea4f669231029`. No frozen bytes were edited. All writes stay inside this lane; no SSH, Orchard, Git, GPU or deletion command ran.

The report applies the no-archaeology writing rule. The frozen-copy comparison is retained because the brief explicitly requests it.
