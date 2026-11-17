B1 implements candidate-only selector decoding, per-call diagnostics, and optional own-depth snapshots. Both package variants build, but **the delivery is not ready for submission**: G1 and the runtime portion of G2 lack a Python environment with Torch, pytest and safetensors. The full restore also lacks its large dependency archives.

The patched payload is `work/p`. Inputs under `in/` remain read-only. `PATCH.diff` applies relative to the payload root. `h1eval/reader_core`, the selector weights, all candidate producers, and the formatter remain unchanged.

The reader accepts `stage1_select_rule` in read settings. `null_argmax` is the default. `candidates_argmax` takes the argmax of the first N head slots, with PyTorch's first-index tie rule; an empty socket returns no candidate without evaluating the head. The rule is explicit in the environment binding and runner IDENTITY, and the package plan pins it. The identity test refuses a rule change before launching a worker.

Each valid box-ground call carries its own `stage1` object through `CallHook.report()` into the output record. It includes 32 retained-proposal counts, retained maxima, lift entries, lifted proposals, `lift_reasons` from the producer's outcome list, linked-candidate count, and up to 30 candidate IDs, frame lists, peaks, logits and float32 feature lists. It also records the null logit, chosen index and whether null won the unrestricted argmax. On empty candidates the head is not evaluated: `null_logit` and `null_would_win` are JSON null. Gap records carry operand states and their last selection counts. The diagnostic cap changes only the record; selection still considers every candidate.

`save_own_depth` defaults to true and is part of the read binding. After generation, the launcher saves float16 own depth with pose9, gravity, grid coordinates, camera matrices and anchor indices under the shard's `own_depth/`. The read output carries its relative path and SHA256. Grounding reuses its existing own grid; a read without a ground call queries that grid after generation. The saved arrays do not feed any response. Setting the flag false skips the snapshot. The retained geometry uses full precision in the reader.

G1: **BLOCKED**. `work/replay/replay_patched.py` uses the patched StageOne with its rule, through the real socket and formatter. `work/check_replay.py` is prepared to compare ground text, gap text, query choices, errors, diagnostic size and accuracy. The command stops at `ModuleNotFoundError: torch`. The following columns are staged evidence, not new measurements:

| Geometry | Rule | Evidence reads | Evidence not-seen pairs | Evidence not-seen reads | Patched result |
|---|---|---:|---:|---:|---|
| tower | null_argmax | 148 | 54 | 53 | Not run: torch missing |
| tower | candidates_argmax | 148 | 7 | 7 | Not run: torch missing |
| hybrid | null_argmax | 148 | 70 | 63 | Not run: torch missing |
| hybrid | candidates_argmax | 148 | 7 | 7 | Not run: torch missing |

| Geometry | Record clean program MRA | Record rescued program MRA | Patched result |
|---|---:|---:|---|
| hybrid | 0.500 | 0.496 | Not run |
| tower | 0.646 | 0.534 | Not run |

The evidence has 600 runs, with eight missing-geometry errors for two items, and 294 covered pairs on 148 successful reads per variant. The replay driver preserves those jobs, so the checker will report mismatches rather than remove failed items. The 7-pair and 7/148-read claims remain unverified for this patch. Cached SAM proposals and hybrid G3T depth are proxies; they do not prove own-depth GPU behavior.

G2: **PARTIAL**. Four structural/identity checks and six stub-method checks pass. The null rule uses the same full-slot `torch.argmax` and `-1` mapping as H1-0. The socket's decision method and all lifting, linking, feature production, boxes and printed response functions are byte- or AST-identical. Diagnostics add observations and never feed the choice or formatter. The tests compare the patched and original selection methods on 69 synthetic slot arrays, cover ties and empty candidates, and reject off-by-one, ignored-rule, ignored-settings and printed-format mutants. These are stub tests, not real Torch or b04 fixture parity. `work/test_b1.py` contains the pending runtime, JSON-size, report-survival and depth round-trip checks.

The b04 suites cannot start because pytest is unavailable. The staged tar also omits its tokenizer, K1 tower/cache fixtures, trained scale/selector data and proof geometry. `work/run_existing.py` redirects absolute fixture references into W and supports baseline and patched runs. The package headcall/ground suites still need their dependencies and external fixtures; they have not been claimed as passed. No CPU first batch has run.

G3: **PASS for the scoped static delta**. The EAT-1 scanner reports 26 findings before and 26 after in changed decision-path files, with no new semantic finding. The before/after whole-file scans report 199 and 190 findings. A text-based comparison also notices the unchanged 0.3 floor on a renamed assignment. Other new raw findings are build-time inventory reads and post-generation snapshot naming/hashing. `EAT1_GATE.json` states the scope, exclusions and comparison key; `EAT1_before.json`, `EAT1_after.json` and `EAT1_new.json` preserve raw evidence. No allowlist was modified. The selector rule adds no fitted constant, threshold, alias table or decision-path file read. Existing reader findings prevent a whole-reader EAT-1 PASS claim.

`b1_report.py` accepts the two returned items files, an item manifest, and optional `--pairs-cache`. It reports call stages, capped/not-seen reads, task MRA, paired room bootstrap intervals (10,000 draws; seed 20261115), metre-only results, each gap's metre error, and name/dataset tables. It prints the pre-registered predictions beside observations and reports missing diagnostics. Its fixture passes. A compatibility check using the staged H1-0 return as both inputs gives 150 reads, task MRA 0.200, 43 metre items, metre MRA 0.297674, 63 not-seen reads and 33 capped reads; its paired difference is zero. `REPORT_BASELINE_SELFCHECK.json` is a self-check, not a candidates-rule result.

Both kits select `object_abs_distance`, arm `own`, mode `none`, and the 150 baseline items. The code archives preserve the complete staged inventory, including nested selector input modules. They build through `orchard_h10/build.py`. The local empty-root rehearsal checks every payload pin, creates the package's bind-source directories, validates descriptors, and checks exact worker arguments. Its log is `REHEARSAL.txt`. It does not execute bwrap, restore, SAM or a language model and is not equivalent to the full H1-0 rehearsal.

The input descriptors retain original archive pins. **Policy input restaging is required:** the inherited `q/policy.json` attests script paths under the original token, so replacing the token in the descriptor alone cannot satisfy the unchanged policy-receipt check. The orchestrator must verify and reissue that receipt for each new namespace and authenticate the replacement archive. It must also verify environment wrappers after relocation. These checks must precede a real CPU restore and the package's operator `check`. No submission receipt has been minted here.

Package pins:

- `c4d7e0a91b28f`: PACKAGE.json SHA256 `69d2465d90622507673100ee988b0bea16ebc426822407d5321f73bd953a38bd`; payload SHA256 `ab5a313f534a8b0b38c2bf43246ffb0e2535a25e7ecb56cd397d3615f4f27e2c`; plan `6f2ee5bd61e6d26db6317579dfeda51617a2871a8b754466497cda98bb44ef69`.
- `d8a2f6c09e137`: PACKAGE.json SHA256 `9c8b32882ccbf5199649e5c908c76dbaaf7561a24e91e50a2503d941f3e6e3a2`; payload SHA256 `686307718a4350b15a91f3abf5422e5e58677c6f0bf0e19febbed12a98e9012d`; plan `329dd72a0581d96758603e637bc14f45ef046c7b961310acd0509e2da27f060d`.

After the runtime gates, fresh input receipts, complete restore rehearsal, and cross-family review pass, the orchestrator can stage each directory under `/project/community/jjyeung/<token>` and run these exact commands on Orchard. They were not executed:

```bash
cd /project/community/jjyeung/c4d7e0a91b28f
/usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 01:45:00
/usr/bin/python3 -I -s -B 3.py submit --gpus 1 --time 01:45:00
cd /project/community/jjyeung/d8a2f6c09e137
/usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 01:45:00
/usr/bin/python3 -I -s -B 3.py submit --gpus 1 --time 01:45:00
```

The job names are `a15_cot_apc4d7e0a91b28f` and `a15_cot_apd8a2f6c09e137`. The estimate is about 2.5 H100-hours total (300 reads at about 25 seconds plus loading); the two suggested walltime reservations total 3.5 GPU-hours. No dollar rate was supplied or fetched.

The orchestrator should obtain one cross-family review before submission, as B1 requests. The review should check selector-slot indexing, settings propagation, metadata isolation, snapshot timing, resume refusal, the narrowed read plan, and retokened inputs. Admission and legality logic are unchanged; the read selects a different route rule. `REVIEW_REQUEST.md` records the request.

File hashes (before → after):

- `b/e2e_reader/grounding.py`: `d9b7e6f3a97e7e5afd8de1f08c13e5357e307f60d6fc2d729069efdbac435d98` → `d8fe3c617a2cba4f01527947826cceb2a923a4725bc3b9dd8b18a889e9c332c4`.
- `b/e2e_reader/servers.py`: `3cd2e6db3b0e57a4b2a63a03418e7a06f67b509c2801370b9dd46e2a2818cedf` → `9e2b9584b466bbfd7e1f7b9ea5a5dde5553eddac1d51ebea6d35c32d679a5097`.
- `b/e2e_reader/stage1.py`: `dc9c918960295c0efbefcd253eb3fb0f3887ed02c1c0cac64da6f5058e8f77ac` → `bee02c481185f5ae9ccfd8bdb7b3616a9fd492aca649bf400edbc80774099f74`.
- `h1eval/h10/depth_snapshot.py`: `new file` → `4a0d36b7d4e003ef60c4b201139e02d8589303b26d49e0bd5e28957ecebdacb6`.
- `h1eval/h10/launch.py`: `40bb4425b48d0d980129940ca7fe23b6718d3d02713c2f1302369bd479d69b94` → `7d6b24baf1db2a280d8dbfbb86c837c1c1e64c695ed9b72c10d1a34ce1fa49c0`.
- `h1eval/h10/perception_own.py`: `0b6665788b59699df015b82c555c5401949268060973d0b2819cd08b78ee1234` → `b669c9e1f550fcaf1bb3702f8a1c6fda78b1c26b03f29cabef5eb0997ea49ea7`.
- `h1eval/perception.py`: `7c2e0e9552b90132b59f620852dbcc556a4c05be7bc8ccfce0486d849776ed59` → `2880395fddeb7ee52144ee6be9e635482420a246a587268420a63266e9522fc9`.
- `orchard_h10/build.py`: `488730c9881049019dd4781a1373e591d0a61d5bb6a87650d98ce6a0a8d95464` → `df7cc62a80b5487aabe4d0e80eb4096226e0dbb15d7a982b9e0c5a5ad4c8f09d`.
- `orchard_h10/job.py`: `7595d0cd2852be3b8c27c2d987404ac9eaf3fe976d31ccda00827b5961f07815` → `5df94799263b7d1ed9a3c4c95e6d4417d5347ca9a07342c6976370d78f3fe06a`.
- `orchard_h10/prepare.py`: `33c6b828c6cee95434020115abb959b532a648a02f464f96062eae0c24e6c57f` → `afa1412fceda4c52fe910a5d241f125c16eb2fabac2b7a56a97a3b7c77c41456`.
- `orchard_h10/runner.py`: `f533bfead435f210b778cc56697a14ef9944499e9159a519950cf96df5a6552e` → `0902daaf7397f3b42800de857f04d53199bafb77a045dbb1d728ea52c6555e76`.

The workdir uses approximately 0.892 GB of regular-file logical bytes, below 5 GB. No deletion was performed. Temporary paths are listed in `REMOVAL_CANDIDATES.md`. All generated files are inside W; one mistyped log-redirection attempt outside W was refused by the filesystem and wrote nothing.

The report uses the no-archaeology and summary writing rules. The before/after comparisons above are retained because they are required compatibility evidence, not project history.
