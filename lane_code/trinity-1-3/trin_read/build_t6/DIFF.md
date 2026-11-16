# Changes against build_t5

The baseline is `/scratch/jjyeung/orch_n30/trin_read/build_t5`. PATH/ENV marks relocation or execution/test-environment changes. BEYOND marks behavior, validation, and new interfaces. The comparison uses bounded file reads, without Git.

| Path | Class | Change |
|---|---|---|
| `trinity_read.py` | PATH/ENV | Uses build_t6's stub and `root/trinity_runner_t6`; installs the expanded wrapper bundle. |
| `trinity_read.py` | BEYOND | Adds `items` and opt-in `--link-models`, linked disk reserve, CPU dry binding, read-only mounts, and CARD/EXIT model audit. Isolated read packets use attempt `a0`; proof attempts stay unchanged. |
| `done_record.py` | BEYOND | Strict shared plain-text/JSON parser; exact object/run/step, positive bytes, lowercase SHA256, and no duplicate/extra fields or extra text lines. |
| `milestone.py` | BEYOND | `stage-export` uses the shared parser and requires object identity to match run/step. |
| `items_export.py` | BEYOND | Imports SHA-pinned, unchanged scorer functions; checks packet hashes, full e193 membership, fixed A544 and optional `--a` alignment; publishes ITEMS and its receipt without overwriting existing outputs. |
| `model_links.py` | BEYOND | Authenticates model manifests, creates hard links without a cross-filesystem copy fallback, writes kit identity receipts, builds read-only binds, and checks hashes/inodes after execution. |
| `namespace_worker.py` | BEYOND | Adds a CPU dry-bind action and hash-checked reuse. COMPLETE authenticates B2048 report and journal bytes. |
| `launch_gcs.py` | PATH/ENV | Replaces launch_pull2's remote source with four ordered GCS URLs and the specified gcloud executable. |
| `launch_gcs.py` | BEYOND | Reads the strict done record and requires its bytes and SHA256. Preserves the stopped-bash gate, ratelimit member, governor registration, wait, registry done rename, receipt, and no-retry behavior. Refuses existing outputs. |
| `README.md` | PATH/ENV + BEYOND | Gives build_t6 paths, the milestone operator sequence, exact scorer journal layout, link mounts/reserve, and test instructions. |
| `tests/conftest.py` | PATH/ENV | Collects top-level test modules; skips retained evidence directories and their deliberate cyclic links. |
| `tests/test_followup.py` | PATH/ENV | Expects runner_t6 and the expanded module manifest; preserves the existing assertions. |
| `tests/test_t5b.py` | BEYOND | Uses the required bucket-free q8 object in the archive fixture; preserves staging assertions. |
| `tests/test_t6.py` | BEYOND | Adds 44 CPU cases for strict admission, scorer conversion/refusal, hard-link integrity/integration, binding reuse, and fake governed downloads. |
| `DIFF.md`, `REPORT_T6.md`, `INPUT_PINS_T6.json` | BEYOND | Records the requested comparison, delivered contracts, verification limits, and input/module hashes. |
| `TESTS_T6_*.log`, `tests/t6_*` | BEYOND | Retains CPU test results and fixtures. No old evidence is removed. |
| `compact_items.py`, `build_t5/` inside build_t6 | BEYOND | Additional artifacts found in the target, preserved without modification. Neither belongs to the installed runner or tested CLI path. The active exporter is `items_export.py`. |

Without `--link-models`, the reader retains its model copies. The hard-link mode supports staged snapshot bases and C1 exports; archive models such as f17 require copy mode. The unchanged kit reuses model identity receipts only after the wrapper authenticates linked content. The original full export checker still runs before generation.

The accepted reader/adapters, scorer implementations, export checker, e193 inventories, decoding settings, label rules, and proof code remain unchanged. No staged runtime, production model, frame store, or cont_ops source was edited.

The requested baseline comparison is the only historical framing retained in this ledger.
