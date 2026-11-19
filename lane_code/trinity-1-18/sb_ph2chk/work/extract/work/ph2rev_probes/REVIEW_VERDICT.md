# sb_ph2rev: phrase kit part 2 (sb_ph2fix.tar) review verdict

**GO AFTER FIXES.** The GPU pass is sound. Fixes 1 and 2 go in before the GPU launch; fix 3 goes in before the CPU aggregate. Each fix needs a re-stage, a re-tar and a new sha256.

**Verified** (evidence under `work/`):
- Tar sha256 matches. 32,742 of 32,742 members match the manifest in bytes and sha256 (13.217 GB), and every source is on /scratch. Suites on the extract: part 1 26/26, part 2 20/20, launcher 23/23; dry-run steps 1–4 PASS. BARS_PART2 sha 166be15b… is unchanged.
- Guard (`GUARD_ATTACK.json`): missing or altered bars, a planted `PER_ITEM_PART2.jsonl`, nested, hidden, `.tmp` and decision JSON files, and KILLED or STOP markers each make all 8 entry points refuse, with 0 writes.
- Real launcher chain on CPU (fake nvidia-smi, real wait): the two readings came 300.06 s apart and both are in the receipt. The chain timeout → vnice → terminator → gpu_inner → step5 ran and stopped at "part 2 needs CUDA"; the launcher wrote KILLED.json and kept RUNNING. A relaunch over RUNNING or partial output refuses with 0 writes. strace shows 0 writes outside `out/pool_part2`.
- Arms (W_cf, W_exact, W_new, R_cond) and bars (exact_holds, new_worth, retention_worth, phrase_safe on both-good rows) match BARS_PART2.json and the spec. All five exclusion pins match. Only withheld-80 has hits (5 captures, 25 rows), leaving 1,012 decision rows; these 5 equal the kit's `WITHHELD`. Nothing held-out, R0-dev, dev-S1 or official is staged or opened.
- CPU first batch (`logs/cpu_first_batch.jsonl`): the shipped `tower()` stops at its CUDA check. Behind a harness-only CPU tower, upstream SAM 3 also needs CUDA at `position_encoding.py:55` and `decoder.py:283` (model build) and at `geometry_encoders.py:648` (`pin_memory`, forward). With shims, CPU bf16 encodes at 9.4 s/frame and detects at 1.44 s/frame. CPU STEP5 fails 11 of 64 frames against the GPU-made cache (presence within 0.047, reader parity holds); the GPU STEP5 is fail-closed. `run()` on capture 1 (4 calls) wrote `candidates.json` and `PART2_RECEIPT.json`, and `launch_part2.sh capture` priced it with 0 refused. In this run's strace, the only /data read is `openssl.cnf` (fix 2), and there are 0 writes outside the pool.

**Fixes (exact edits):**
1. vnice preemption is broken: `vendor/terminator.sh` puts its stop file in `out/pool_part2` (mode 775), where other users cannot delete it. Copy `/scratch/jjyeung/orch_n30/sb_cafix/kit_v2/vendor/terminator.sh` over `part2/vendor/terminator.sh`, and set its sha in `part2/vendor/PINS.json` (lines 4 and 8) to `19727987d5517c0e2549e1205e55f4bcc87f34dafe66c96bdf90233305942e5d`. In the launcher write-tree test, allow `/tmp/terminator/$USER-<pid>` as the one write outside `out/pool_part2`.
2. The pass reads /data2. libcrypto's built-in OPENSSLDIR makes every payload Python open `/data2/jjyeung/envs/sam3/ssl/openssl.cnf`, and an inherited PATH adds 92 failed /home lookups. In `launch_gpu.sh`, line 4, add `export OPENSSL_CONF="$PWD/../payload/environment/ssl/openssl.cnf"`. In `launch_gpu.py` `environment()`, line 93, add `OPENSSL_CONF=str(kit.parent/'payload/environment/ssl/openssl.cnf'), PATH='/usr/bin:/bin'`. Tested: Python with ssl, hashlib and torch then touches /home or /data 0 times.
3. Population (fix before the aggregate, because the guard allows one run). `price.aggregate` decides on 1,037 rows and 456 both-good rows and fits W_new on all 209 captures; line 242 asserts against part 1's top-level `both_good_rows`, which is 456. Wrap lines 239–289 in `population(keep, fc)` and call it twice: once with `keep = c not in AG.WITHHELD` and `fold_choices` for the plain keys (assert 1,012 rows, 204 captures and 442 both-good against `part1['population']['decision']`), and once with all captures and `fold_choices_1037` for the `_1037` keys. In each call, W_cf rows, good_rows, the W_new fits, `best` and R_cond use only kept captures. Add a fixture test that reproduces part 1's W1 +3.82 [+2.16, +5.63] on 1,012 rows.

**Advisory:**
- A refusal at the idle readings leaves RUNNING and KILLED.json, so the pool stays refused; rename `out/pool_part2` aside before retrying on another card (no budget is spent by then). Ctrl-C to the launcher kills only `timeout`, leaving the pass bounded by its own deadline and watchdog, so run in tmux and stop through the terminator file.
- Four planted files get past the guard: a dangling `PER_ITEM_PART2.jsonl` symlink (the aggregate's open follows it), a symlinked directory, a `*.JSON` file and a `*.csv` file. In `gate.py`, refuse symlinks and match suffixes case-insensitively; in `price.py`, open outputs with `'x'`.

**Claims not backed by files:**
- The staged smoke's claim that external inputs are blocked, since its audit hook misses native opens (fix 2). The real launcher chain, since the builder's tests inject a fake `run`.
- No route home is given: pricing needs trinity-1-18's 209 K1 caches (only 1 is staged), and `run.sh` hardcodes the path. The 0.88 GPU-h reuses K1's 0.064 s rate, which spreads encoding over about 19 prompts per capture; this pass has 7.4.

**GPU need:**
- Card: one idle card of at least 48 GB (A6000 or 6000 Ada), compute capability ≥ 8.0, bf16. CPU peak RSS was 8.7 GB.
- Time at the spec rate: 0.88 GPU-h by default (1,540 calls) and 1.14 with `--all-aliases` (2,004).
- Time at the measured encode:detect ratio of 6.5:1: about 1.23 GPU-h by default, so the projection at 10 captures likely drops the new phrases (W_new MISSING) and finishes in about 0.91 GPU-h. With `--all-aliases`, 1.43, dropping to 1.11.
- Stop: 1.2 GPU-h (4,320 s). Staging: 13.22 GB extracted (tar 13.41 GB), plus about 0.5 GB of output.

**Launch** (default mode, same path on the GPU node); afterwards, return the pool and price on trinity-1-18 in `sb_mask_phrase`:
```
ssh trinity-1-18 'cat /scratch/jjyeung/orch_n30/sb_ph2fix/out/sb_ph2fix.tar | ssh trinity-X-Y.ib "mkdir -p /scratch/jjyeung/orch_n30/sb_ph2fix && tar xf - -C /scratch/jjyeung/orch_n30/sb_ph2fix"'
tmux new -s p2 'env PATH=/usr/bin:/bin bash /scratch/jjyeung/orch_n30/sb_ph2fix/sb_mask_phrase/part2/launch_gpu.sh --node-local <idle index>'
ssh trinity-X-Y 'cd /scratch/jjyeung/orch_n30/sb_ph2fix/sb_mask_phrase/out && tar cf - pool_part2 | ssh trinity-1-18.ib "cd /scratch/jjyeung/orch_n30/sb_ph2fix/sb_mask_phrase/out && tar xf -"'
bash part2/launch_part2.sh capture && bash run.sh part2/price.py aggregate   # aggregate only after fix 3
```
Conduct: during a guard test, my harness's subprocess timeout killed my own sandboxed launcher in its 300 s wait, before any pass child existed; I also ran one read-only nvidia-smi query.
