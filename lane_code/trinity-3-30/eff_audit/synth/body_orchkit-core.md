# Build brief 3 of 8: orchkit-core (lane `eff_orchkit_core`, branch `eff/orchkit-core`, Claude Opus, effort high, size L: 12 to 16 agent-hours)

Build the shared kit library in the repository: one pin manifest, one launcher, one stager, one return path and one ledger, so that a new job is a new config and not a fork of a launcher.

## Why

- The Orchard launcher was forked, not configured: `orchard_launcher.py` exists in 9 distinct copies (plus 2), `orchard_results.py` in 5, `chain_save.py` in 5; the forks differ in constants written into code, such as `config['spec']['step']!=544` and a pool path. Each fork needs a line-range `DIFF.md` and a review that reconstructs the kit (`AUD/kits/INVENTORY.md` sections 2 to 4; `REF/trinity-1-3/cont_ops/work/d0/readk/DIFF.md`).
- Hashes of one file live in several places, and one of them goes stale: "The checks involve 21 duplicate-pin groups, and the copies disagree in 2 of them"; "Every later builder ... deep-copies the old value" (`distill_design/ROUTED_READ_PIN_GRAPH_AUDIT_20261114.md`, lines 1 and 43). Pilots 169537 and 169589 were lost that way, each a cycle of 1.5 to 2 h.
- Job ledgers sit on single nodes in 5 schemas, and those on trinity-2-18 and 2-28 are gone.
- The same helper is defined again and again: a sha function in 179 distinct files, a pin check in 65, `opaque.py` vendored 85 times.

{{COMMON}}

## Scope (formats are fixed in `AUD/briefs/INTERFACES.md`; build to them)

**`pins.py`** (Trinity). `pins.py build --root DIR --spec SPEC.json --out PINS.json` writes an `orchkit-pins-v1` manifest from files only; `pins.py verify --manifest PINS.json --root DIR` names every entry that differs; `pins.py audit --kit OLD_KIT_DIR` reports, for a kit of the old style, each group of places that record one file's hash and whether they agree. Invariant, enforced by a test on every packed kit: no 64-hex string equal to an entry's sha256 occurs anywhere in the kit outside `PINS.json`.

**`anon.py`** (Trinity). One opacity check for everything bound for the batch host: file names, text bytes, members of nested tars, the rendered script, argument and environment names and values, the job name. Port the rules of the tree kit (`AUD/repo/sealed_tree_b01ce449/launch_s1/b/opaque.py` and an `ANON_OK.json` under `REF/trinity-1-3/cont_ops/work/d0/orch_r8/`). The word list is `tools/orchkit/ANON_WORDS.txt`; it stays on Trinity and GitHub and is never packed.

**`pack.py`** (Trinity). Assembles a kit directory: the family's code, CONFIG, `PINS.json`, and the job-side modules (`util.py`, `stage.py`, `ret.py`) copied into a package whose name the config gives (default `lib`). The name `orchkit` never ships. Job-side modules import one another relatively and pass `anon.py` themselves.

**`launch.py`** (Trinity). One launcher with four subcommands.
- `prepare --kit DIR --config CONFIG.json --out PREP/`: validates the config against the family schema; verifies the pins; requires a `DRYRUN_REPORT.json` with verdict PASS whose `kit_pins_sha256` and `config_sha256` equal the kit's (or `--no-dryrun-reason TEXT`, which the ledger row records); runs `anon.py`; records the commit through `tools/provenance.py` as the existing launchers do (read it in `W/clone`; a provenance refusal is a refusal of prepare); renders the batch script from the one template; mints the job name with one function; appends the ledger row `minted`; writes `PREP/SUBMIT.json` with the exact submission argv. Prepare contacts nothing.
- `submit --prep PREP/ --go GO_FILE`: refuses unless the GO file exists and names the job token; refuses when the ledger shows one of our jobs live on a one-job partition, unless the GO file says to queue behind it; prints the command; runs it through `ORCHKIT_OSSH` only with `--execute`. You never pass `--execute`. The submission script checks, in the same call and before `sbatch`, the home quota and the pool's free space on the batch host against `CONFIG.budgets`, and submits nothing when either is short (on 2026-11-15 a full home quota made every write there fail, returns included: `B/events/evalx27/20261115T1732Z_BLOCKER_orchard_home_quota.md`); a kit stages nothing under the batch host's home directory.
- `status` and `fetch`: thin wrappers over the same transport, tested with a fake.
Every per-run constant (step, artifact digest, pool, families, partition, GPUs, time) comes from `CONFIG.spec` and `CONFIG.job`. Write `examples/read_step.config.json` holding the constants that the D0 read kit fork hard-codes, as the proof that the next read needs no fork.

**`templates/job.sh.tmpl`.** One batch script: partition, GPUs, CPUs, memory, time, the signal sent before the limit, nice, a CPU-only guard, the entry argv; `set -euo pipefail`; the system `python3` until the environment is active. Its standard output and its return never depend on the project filesystem, which other tenants can fill.

**`stage.py`** (batch host, 3.6-safe). Stages every pin entry by type (`file`, `tar`, split `parts`, `gcs` object by generation, `orchard` pool path) with a sha check on each. One safe extractor refuses absolute members, `..`, links that leave the destination and duplicate members. Each destination declares a collision policy: `new` (must not exist), `disjoint` (may exist; no member may collide), `same` (identical bytes allowed). `stage.py --rehearse` lays out the complete logical tree on CPU with stand-ins and reports every collision before a byte moves.

**`ret.py`** (batch host, 3.6-safe). One return path: a tar bounded by the config's budget, published to the pool and, independently, to GCS through a resumable session upload with ranged reopen after a reset; one receipt (`{token, job_id, state, members: [{path, bytes, sha256}], pool, gcs: {uri, generation}}`); a failed job still returns its traceback, because the return runs when staging or the entry fails. Port the behaviour of `REF/trinity-1-3/cont_ops/work/d0/readk/kit/launcher/` (`chain_save.py`, `orchard_results.py`, `return_io.py`, `stdout_transfer.py`) and of the tree kit's `launch_s1/b/gcsput.py`; state in REPORT.md each behaviour you kept, changed or dropped.

**`ledger.py`** (Trinity). `append`, `lookup --token`, and `import --from OLD_LEDGER --lane L`, which maps the five old schemas (`AUD/kits/INVENTORY.md` section 3, row "Ledger") to `orchkit-ledger-v1` rows. Run the import over the ledgers in REF into `W/out/ORCHARD_LEDGER.imported.jsonl`; the orchestrator decides whether that file becomes `B/ORCHARD_LEDGER.jsonl`. You never write the production ledger.

**`util.py`.** You own it. Change it only by adding functions, with tests, and say so in REPORT.md.

## Files you own

`tools/orchkit/pins.py`, `anon.py`, `ANON_WORDS.txt`, `pack.py`, `launch.py`, `stage.py`, `ret.py`, `ledger.py`, `templates/`, `schema/`, `examples/`, `util.py` (additions), and `tests/test_{pins,anon,pack,launch,stage,ret,ledger}.py`.

## Tests (folder `tools/orchkit/tests/`)

1. Pins: build and verify round trip; one changed byte names its entry; a repeated `logical_path` is refused; the single-place invariant fails on a kit with a copied hash; `pins.py audit` over the recovered native kit (`REF/trinity-3-30/recover_k1/work/code4d/sj/orch_cd/evalx/work/milestone/orchard_native/`) reports its duplicate groups, and REPORT.md compares the count with the audit's 21.
2. Launch: the job name matches `^a15_cot_ap[0-9a-f]{16}$`; prepare appends exactly one ledger row; prepare refuses a missing, failed or mismatched dry-run report, a schema-invalid config, an opacity hit and a provenance refusal; submit refuses a GO file that does not name the token; without `--execute` the fake transport records zero calls; with a fake transport that reports a short quota, `sbatch` is never reached.
3. Template: rendering `examples/read_step.config.json` and a config equivalent to the tree kit's job gives scripts whose partition, GPUs, time, signal and entry equal those of the existing `job.sh` files; REPORT.md lists every remaining difference.
4. Stage: each collision policy; two entries with policy `new` on one directory fail the rehearsal and name both (the 169477 `[Errno 17] File exists` class); unsafe members are refused; a sha mismatch names the entry.
5. Return: a return above its budget refuses before any upload and lists the members; a reset in mid-upload resumes by range against a fake server; a job whose entry raises still returns a receipt with the traceback.
6. Opacity: a word planted in a member of a nested tar is found; the packed toy kit holds no listed word and no Trinity path.
7. The suite passes on `/usr/bin/python3` and under the bwrap run of rule 8.

## Deliverables

Branch `eff/orchkit-core` (commit the manifest, util and ledger first, so the other builds can read them); `W/out/ORCHARD_LEDGER.imported.jsonl`; `W/REPORT.md` with a migration note for the next read kit and the next tree kit; the RESULT event; the result block in RECORD.

## Out of scope

The dry run (kit-dryrun), the reader (reader-harness), the watcher (orch-watch), governed streams (govstream); converting any existing kit, which stays byte-identical until its next epoch; any contact with Orchard or GCS; writing `B/ORCHARD_LEDGER.jsonl`.

## Review

One independent review before first use, limited to `anon.py`, the job-name function and `launch.py submit`, because they carry the opacity rule and the rule that no job is submitted without a GO naming it. Ask for it in the RESULT event.
