# orchkit-core: build report (branch eff/orchkit-core, head 633e3d0b)

## What I built

`tools/orchkit/` on branch `eff/orchkit-core` (clone `/scratch/jjyeung/orch_n30/e_orchkit-core/repo`), six commits queued in `PUSH_QUEUE.txt`:

| Commit | Content |
|---|---|
| ba83eb47 | `util.py`, `__init__.py`, `tests/test_util.py` (skeleton, sha256 equal to INTERFACES), `pins.py`, `ledger.py`, `anon.py`, `ANON_WORDS.txt` and their tests |
| 2afc8236 | `stage.py` (job side): staging by entry kind, policies new/disjoint/same, rehearsal, safe extractor |
| 76ddbe90 | `ret.py` (job side): the job driver and the one return path (bounded tar, pool, GCS resumable session upload with ranged resume, receipt) |
| 4ef7a925 | `launch.py` (prepare/submit/status/fetch), `templates/job.sh.tmpl`, `pack.py`, `schema/` (header, `read`, `generic`), `examples/read_step.config.json` |
| e263c512 | submit also refuses, on the batch host, when `squeue` shows one of our jobs live on a one-job partition |
| 9d58cab7, 7a3a4cf8, 4601700f, cb6a5f04, fbe5ece7, 9e1313f6, 5b3301f2, 3c731cbc, 633e3d0b | fixes for review findings OC-01..OC-31 (see "Review") |

`util.py` is unchanged; I added no function to it.

How a job runs: `pack.py` assembles KIT (family code under `code/`, job-side `util/stage/ret` under the package the config names, default `lib`; the name `orchkit` never ships), writes `PINS.json` and sets `CONFIG.kit_pins_sha256`. `launch.py prepare` checks everything, bundles KIT plus a per-job `JOB.json` (token, job name, GCS session URIs) as a deterministic gzip tar embedded in hex in the batch script, and writes `PREP/{BATCH.sh,SUBMIT.sh,SUBMIT.json}`. On the batch host, the script's bootstrap (system `/usr/bin/python3`) unpacks into `<root_parent>/a_<jobid>_<token>` on node-local disk and `exec`s `python3 -m lib.ret job`, which stages `CONFIG.stage`, runs `CONFIG.entry`, and always returns `out/` and `logs/`.

## Tests (all in `tools/orchkit/tests/`, `TMPDIR=W/tmp`)

- `cd tools/orchkit && /usr/bin/python3 -m unittest discover -s tests` (3.6.8): `Ran 108 tests in 7.842s` / `OK`.
- `HOME=/tmp bwrap --ro-bind / / --bind W W --tmpfs /home --tmpfs /data --tmpfs /data2 --tmpfs /data3 --tmpfs /tmp --dev /dev --proc /proc /scratch/jjyeung/envs/p1cpu/bin/python -s -m pytest -q -p no:cacheprovider tests`: `108 passed in 7.69s`.

Per file (108): util 10, pins 15, ledger 6, anon 21, stage 11, ret 8, pack 6, launch 31. The brief's test list maps as follows. (1) Pins: round trip, one changed byte, repeated path, copied hash, stale hash, record field must equal its own entry, nested tar; the audit test runs over the recovered native code and the VSTI kit. (2) Launch: the name regex over 200 mints; exactly one ledger row; refusals for a missing, failed or mismatched dry run, a schema-invalid config (header and family), an opacity hit, a provenance refusal (and `/home`, `/data*` checkouts), an unpinned or changed kit file; a GO file that does not name the token; zero transport calls without `--execute`; a short home quota and a missing pool reach no `sbatch` (the fake transport runs the real `SUBMIT.sh` under bash with fake `sbatch`/`squeue`). (3) Template: see below. (4) Stage: each policy, two `new` items on one directory fail and name both, seven unsafe member kinds, a sha mismatch naming the entry, parts, gcs by generation through a fake fetcher. (5) Return: an over-budget return refused before any byte with members listed largest first, a mid-chunk connection reset resumed by range against a fake GCS server, an entry that raises and a staging fault both still return a receipt with the traceback, a GPU job without devices, a failed pool channel. (6) Opacity: a nested tar member and the packed toy kit (no listed word, no `/scratch/` path, no `import orchkit`). Two further tests run the rendered `BATCH.sh` locally under bash with `SLURM_JOB_ID=77`: it unpacks, stages, runs the entry and returns to a pool directory, and a `SIGUSR1` sent after 3 s interrupts the entry and still returns (state `interrupted`).

## Template against the existing jobs

Rendering `examples/read_step.config.json` gives partition `general`, `--gres=gpu:1`, `--cpus-per-task=16`, `--mem=200G`, `--time=06:00:00`, `--signal=B:USR1@300`, `--account=mt01`, `--output=/dev/null`, equal to the D0 read kit's `submit_argv` (parsed from REF `readk/kit/launcher/orchard_launcher.py` in the test). A tree-kit equivalent config renders the partition, GPUs, CPUs, memory and signal of `launch_s1/b/jt8c.sh`. Remaining differences:
- Time is rendered `1-00:00:00` where `jt8c.sh` writes `24:00:00` (same limit).
- The tree job sends output to `/home/jjyeung/okit/x/.../o/%j.out`; ours sends Slurm output to `/dev/null` and keeps `logs/driver.log`, `stage.log`, `entry.log` on node-local disk, returned with the result. Nothing goes to the batch host's home directory.
- `jt8c.sh` computes an argument on the batch host (`m=$(python3 r8.py ...)`); a config entry is a fixed argv with `{root}`, `{kit}`, `{out}` substitution only, so that step moves into the family's entry script.
- The read kit passes options on the `sbatch` argv and the payload on stdin; ours writes `#SBATCH` lines and submits a temporary copy of the script in `$TMPDIR` (or `/tmp`) on the login node after `sbatch --test-only`.
- The read kit's `-I` interpreter flag becomes `-E -s -B` for the driver, because `-m lib.ret` needs the kit directory on `sys.path`.
- `jc1.sh` has no `--signal`; ours always sends one (`signal_s` >= 30 s), because the return needs warning time.

## Return and stage behaviour against the read kit and the tree kit

Kept: a byte-capped archive with a writer that refuses growth past the cap (`chain_save.LimitedWriter`); copy to the pool through `.partial` names with a sha check, then rename (`return_io`); two independent channels (pool and GCS) and `returned` when either verified (`orchard_results.publish`); GCS size and md5 checked against the object metadata (`gcsput.upload`); a return when the job fails; the safe-member rules of the read kit bootstrap (no absolute, no `..`, regular files, no duplicates, size cap).
Changed: the budget is checked before the first byte from an upper bound of the uncompressed tar, and an over-budget return becomes a tail-only return (last 64 KB of each log) that lists the refused members; members are every file under `out/` and `logs/` rather than a hard-coded list; GCS goes through resumable session URIs minted on the cluster side (as `gcsput`), but a reset now queries the session (`Content-Range: bytes */N`) and resumes at the persisted offset instead of restarting at byte 0; the receipt carries `kit_pins_sha256` and `config_sha256` instead of a plan hash; the pool budget and free space are checked before the copy.
Dropped: the pool write test at job start (the submission script now probes room before `sbatch`), `gcloud storage cp` and the read-back `.gcs-check` (no Google credential is needed on the batch host), `stdout_transfer` framing (the receipt and archive travel by pool or GCS), `split` multi-part uploads of `gcsput` (one session per object; parts can be added if a return above about 5 GB appears), and the hard-coded 200 GiB project floor of `chain_save` (budgets come from the config).

## Pin audit and the 21 groups

`pins.py audit` over REF `native_r4/builds/01_vsti/out` reports 302 places, 61 groups, 6 disagreeing (`W/out/audit_vsti.json`); over the recovered native code it reports 8 places, 1 group, 0 disagreeing. Neither is a full old kit (REF holds no FAMILY/CONFIG/BATCH/MASK_CACHE set), so, as the verdict requires, I do not compare these counts with the audit's 21. Grouping is by file base name, so several groups (`COMPLETE.json`, `REPORT.json`) collect different files that share a name.

## Formats I added (INTERFACES owners, please confirm)

- CONFIG: optional `family` (selects `schema/family.<name>.schema.json`, default `generic`), `stage` (the stage plan), and `return` (`pool`, `gcs_prefix`, `gcs_env`); `job.account`, `job.root_parent`, `job.package`; `job.partition` also allows `preempt` (the tree kit's partition).
- Read spec: `frames.count` is 32 or 64 (user ruling: frame count is a parameter); optional `families`.
- `ANON_WORDS.txt`: `orchkit` is a name rule plus a text rule that allows only the format identifiers `orchkit-<format>-v1`, which PINS.json and CONFIG.json must carry.
- The submit record `orchkit-submit-v1` (`PREP/SUBMIT.json`) and the return receipt `return-receipt-v1`.
- Ledger rows gain `payload_sha256` (sha256 of the bundle: kit snapshot plus JOB.json). Token claims and per-partition locks live in `<ledger>.claims/`.

## Ledger import

`W/out/ORCHARD_LEDGER.imported.jsonl`: 151 rows from the 11 primary ledgers in REF (cont_ops 12, cont_ops readk 82, native_r4 6, evalx27 4, b06_a2dense 1, k1_ops3 8, k1_ops3 pending 4, b07_offread 34); review and lane copies of those ledgers were not imported. Only 3 rows carry a job id, because the old schemas mostly record tokens; the readk rows from test prepares carry state `test-prepare`. The orchestrator decides whether this becomes `B/ORCHARD_LEDGER.jsonl`.

## Saving, restated as the verdict requires

The saving is an estimate, not a measurement: of the 3 to 6 h per kit, about half (1.5 to 3 h) belongs to this change (no launcher fork, no DIFF.md, one pin manifest) and half to reader-harness.

## Not proven

- No run on the batch host: Slurm's handling of the `#SBATCH` lines, the 4 MiB script limit, `SIGUSR1` delivery to the `exec`ed driver, and `/usr/bin/python3` being 3.6 there are tested only on trinity-3-30 with fakes.
- The GCS protocol is tested against my fake server, which follows the documented resumable protocol; no real session URI was used, and nothing mints session URIs yet (the `--sessions` file must come from the cluster side).
- The room check reserves the whole home and pool budget with `posix_fallocate` on `~/.p_probe` and `<pool>/.p_probe`, then truncates them; whether the batch host's file systems charge quota for a reservation is unverified (on NFS, glibc emulates it with block writes).
- `stage.py` fetches `gs://` entries through `gcloud storage cp` with `return.gcs_env`; untested against a real bucket.
- `flock` on the NFS ledger across hosts, and the import's mapping of free-text old fields into `meaning`.
- Bootstrap failures before the driver starts (payload digest, unpack) leave no return, because Slurm output goes to `/dev/null`.

## Adoption steps for the orchestrator

1. Order the one independent review the brief names: `anon.py` with `ANON_WORDS.txt`, `launch.mint_job_name`, and `launch.submit` (with `submit_script` and `live_check`).
2. Land `eff/orchkit-core` on `main` by fast-forward after the review; nothing running changes, because no existing kit imports it.
3. kit-dryrun: produce `orchkit-dryrun-v1` reports for packed kits; `prepare` reads `KIT/DRYRUN_REPORT.json` or `--dryrun`.
4. Decide on the imported ledger, then set `ORCHKIT_LEDGER` (default is `B/ORCHARD_LEDGER.jsonl`).
5. Provide a session-URI minting step on the cluster side (`--sessions` JSON with keys `result.tar.gz` and `RECEIPT.json`).

## Migration note for the next read kit and the next tree kit

Next read kit: put the reader code in a directory, write a config from `examples/read_step.config.json` (step, export logical path, families and frame count in `spec`; pool and GCS prefix in `return`), list the export artifact and model weights as remote pin entries (`--remote`, kind `orchard` or `gcs` with their recorded sha256) and stage them with policy `new` into distinct destinations, then `pack.py`, the dry run, `launch.py prepare`, a GO naming the token, `submit --execute`. Files named after the cluster (for example `trinity_read.py`) must be renamed, because `pack.py` refuses them. Next tree kit: the same, with family `generic` (or a new family schema), partition `preempt`, and the `r8.py` argument step moved into the entry script; the environment tar stages with policy `new`, data shards with `disjoint`.

## Review

First review (Codex gpt-6-astra, high, read-only; verdict W/work/review/VERDICT_1.json.md): NO_GO with eight verified findings, all fixed in 9d58cab7 with a regression test each that fails on e263c512 and passes now:
- OC-01 opacity missed a gzip tar under a neutral name, five nested compressed tars, a tar header uname, a FIFO body and UTF-16 text. anon.py now detects gzip, bz2, xz and zip by magic, scans tar header fields and the raw archive bytes, scans text again with NUL bytes dropped, and fails closed (a hit) on anything too large, too deep (8 levels), undecodable or special.
- OC-02 the name rule ("split") missed config paths and environment. Every string key and value of CONFIG.json, PINS.json, JOB.json and DRYRUN_REPORT.json is now a name; prepare scans BATCH.sh and SUBMIT.sh as names and passes return.gcs_env as the environment.
- OC-03 lane patterns were case-sensitive and the format-id exception accepted longer names; both fixed in ANON_WORDS.txt.
- OC-04 a token with a trailing newline passed the anchors; every token, job-name and sha pattern now ends in \Z.
- OC-05 a failing squeue let submission continue; the live check now refuses.
- OC-06 the room check probed at most 8 MiB; it now reserves the whole budget.
- OC-07 two submits could both pass the intent check; the intent is now claimed with O_EXCL before the transport.
- OC-08 SUBMIT.sh was re-read after its check; submit now reads it once, checks it and sends those bytes.
Later rounds (verdicts W/work/review/VERDICT_N.json.md, diffs FIX_N.diff), each fix with a regression test that fails on the previous head:
- OC-09 the compressed bytes themselves were not scanned (gzip file name, trailers): fixed 7a3a4cf8.
- OC-10 the single-place check skipped archive raw bytes: fixed 4601700f (it reads raw bytes and header fields and fails on unscannable blobs).
- OC-11 prepare re-read the source kit after checking it; OC-12 submit trusted the token in SUBMIT.json; OC-13 prefixed zips; OC-14 duplicate JSON keys, root strings, UTF-16 hashes: fixed cb6a5f04 (prepare checks and bundles one private snapshot, kept as PREP/kit).
- OC-15 one container reading hid another; OC-16 submit trusted SUBMIT.sh and argv; OC-17 duplicate keys in CONFIG.json: fixed fbe5ece7 (every reading inspected, unsupported containers refused, submit rebuilds both scripts from PREP/kit and PREP/JOB.json, GO must be a line starting with GO).
- OC-18 escapes in UTF-16/32, compressed or extension-less JSON; OC-19 damaged zips; OC-20 a kit swapped between check and bundle at submit; OC-21 two copies of one preparation: fixed 9e1313f6 (text views with escapes resolved, submit snapshots PREP/kit, one claim per token beside the ledger).
- Concurrent submissions to "general" both passed the one-job check (round 7 transcript): fixed 5b3301f2 (a per-partition lock beside the ledger).
- OC-22 partition taken from SUBMIT.json; OC-23 octal, named and slash escapes; OC-24 damaged prefixed zips and bad-checksum tars; OC-26 JOB.json and DRYRUN_REPORT.json not anchored: fixed 3c731cbc. The minted ledger row now carries payload_sha256 (the whole bundle), a field I added to orchkit-ledger-v1.
- OC-25 ("split" in file contents) is a specification question, not a defect: by AGENTS.md "split" is a name rule, and every Python program calls str.split.
- Round 9 (VERDICT_9): OC-01..OC-26 fixed; OC-25 withdrawn by the reviewer under the clarified rule; OC-27 line-continuation escapes, OC-28 gzip header file names, OC-29 damaged tars with non-ASCII names, OC-30 lzma-alone and zlib streams, OC-31 cluster paths with repeated slashes or a bare mount root: fixed 633e3d0b.
Round 10 re-review: in flight (W/work/review/REVIEW_BRIEF_10.md).
