# Selector switch and step-544 tower read kit

Package **e47d0593fefec** carries B1's selector switch and diagnostics on the reviewed bf94 evaluator. Both arms honor the setting. CPU validation passes within the supplied fixture coverage. The kit is ready for cross-family review; no job ran.

**The full read plan is not expected to fit one allowed allocation.** Measured own-arm time is 3.27 hours for 786 reads. Adding the supplied G3T timing gives 7.61 hours of reads, or about 8.11 hours with an estimated 30-minute staging/loading allowance. The unchanged five-hour cap remains enforced. The kit prioritizes distance under both rules, then camera, then room, and returns explicit partial coverage at the deadline.

## Package identity

| Artifact | SHA256 |
|---|---|
| bf94 payload | `4a41299cbcc78a2c57a48b285f43bf19558f747a3584365c96b23e9c9184df3e` |
| New payload, `0.tgz` | `9bd9e343bc9f887a16284385057833d682f2eb0df7db85eda12553796540893e` |
| New plan | `135a67c9571888a67413dfd3d3f460fd67272914dbe2f300dcc41727ef9ddbed` |
| New `package/PACKAGE.json` | `e921b30dbcf1511aebcfdcc0ed51048eb910d0c7ace1e0a1d2ee74b8a99c15d7` |
| New sealed batch | `03d63cb2eb0ac3794751a69a7f871ed0f1f9bbf15973dcf1f6249ac02997ffec` |
| Operator sequence | `68797cec59123bd159d1acf6080cc70b338a0d19de99b6b64a30da713ae466a9` |
| Opaque delivery, `1.tgz` | `1a60c9826f8d3d49081930e12dcf5434a3a876af805c2570585c7c29d4b98c03` |
| Unchanged export pin file | `798111bc92c146f64a1c031827a38381be022ae44304f864cc51f880d2fc754b` |
| bf94 raw step-544 inputs | `93468153b4b4fc781fad664053281f3e92e80e3322eaaf76634f212e45b7c647` |
| All-type operator inputs | `025b4688121ac3df8d5ecf92798b1abadf6f4a8d055eb3980a606915ceea0207` |

The payload has 5,300,495 bytes. `FILE_SHA256_DIFF.tsv` contains before/after hashes for every changed member. Eleven reader or wiring files change or are added; `9.json` changes their pins and the package token. The other 914 members remain byte-identical. `PATCH.diff` is relative to bf94's payload root.

The source builder is byte-identical to bf94. `build_package.py` uses cont_ops's production `orchard_h10.build.build()` path and authoritative inventory, adding only the snapshot module. Production `tar_bytes()` retains sorted USTAR members, file modes, gzip level 6, and zero mtime. `build_operator.py` seals the external operator wrapper into the batch and updates the public descriptor; it does not rebuild or modify the payload. `build_delivery.py` packages the numeric operator files and authenticated inputs.

## Reader behavior and identity

`stage1_select_rule` has two values:

- `null_argmax` keeps the null slot and remains the default.
- `candidates_argmax` selects the best candidate when candidates exist, using the same first-index tie rule. Empty candidates return no selection without calling the head.

`save_own_depth` stays available and defaults to **false**. Default reads therefore retain bf94 decisions and add diagnostics. Per-call `stage1` records survive `CallHook.report()` under their own key; they never feed the formatter or selector inputs.

The rule reaches `StageOne` through the own lazy socket, `h1eval.perception('tower', ...)`, and the production `parity.make_real()` tower path. Tests execute these paths with stub towers/heads and reject a planted tower path that ignores the setting. The arm and rule enter runner identities; launcher bindings also include the rule, settings digest, and snapshot flag. Journal resume and tower reuse refuse cross-rule identities.

AST checks prove identical candidate production after removing the diagnostic assignment, identical null-rule head evaluation/argmax/null mapping, identical socket decisions, lifting functions, and printed responses. All candidate producers, formatters, scorers, statistics, call caps, items, heads, selector inputs, G3T/SAM inventories, admission, restore, export pins, and policy checks remain byte-identical to bf94. `DELTA_AUDIT.json` records the proof scope.

## Validation

`TESTS.txt` records commands, exit codes, and detailed log files, including failed fixture-development checks and their successful final checks. No failure is hidden by a skipped test.

| Check | Result |
|---|---|
| Adapted cont_ops package tests | 14 pass; includes SFT/544 admission, preparation guards, exported identity, and sealed helpers. |
| cont_ops production constraints | 9 pass; retained production-reference checks with the new token for policy tests. |
| B1 runtime tests | 8 pass. |
| B1 stub/mutant tests | 6 pass. |
| Both-arm and production tower wiring | 7 pass, including an ignored-rule mutant and cross-rule tower-reuse refusal. |
| Operator sequence and empty-root checks | 5 pass; worker arguments, settings, identity refusal, partial completion, and bootstrap dispatch. |
| Pairing report fixtures | 6 pass; missing/duplicate keys, rule refusal, strict camera bar, caps, stage table, and repeated-call errors. |
| B1 report fixture | 1 pass. |
| Full b04 suite on the new payload | 31 pass; 3 failures and 10 errors all require absent K1 `tower.npz` fixtures, matching W1's recorded non-passes. |
| Replay against W1's expected traces | All 600 runs; **0 mismatches**. Eight expected missing-geometry errors match exactly. |
| EAT-1 scoped static comparison | 39 findings before and 39 after; **no new semantic finding**. No allowlist changes. |
| Own-versus-own report self-check | Complete coverage and delta 0, CI [0, 0] for all five types and both distance comparisons. |

The replay covers 148 successful reads and 294 grounded pairs per geometry/rule variant. Under `null_argmax`, tower has 54 not-seen pairs and hybrid has 70. Under `candidates_argmax`, each has **7 not-seen pairs in 7 reads**: six SAM-empty pairs and one raster/erosion/crop pair. The largest diagnostic is 32,006 bytes, below 64 KiB. This cached replay does not establish live own-depth or GPU inference parity.

The static scan includes both newly wired tower files. Existing EAT-1 findings remain; this is a scoped change comparison, not a whole-reader EAT-1 pass. Raw findings and exclusions remain in `EAT1_before.json`, `EAT1_after.json`, and `EAT1_GATE.json`.

## Read plan, time, and price

The package keeps one token and one production allocation. The external wrapper schedules:

| Order | Read | Type | Items |
|---:|---|---|---:|
| 1 | Null slot kept | Distance | 150 |
| 2 | Best candidate | Distance | 150 |
| 3 | Null slot kept | Camera displacement | 150 |
| 4 | Null slot kept | Camera rotation | 150 |
| 5 | Null slot kept | Camera movement direction | 150 |
| 6 | Null slot kept | Room | 36 |

Each logical read has its own settings and identity. Type journals live under `0/<type>/metadata/journals/` or `1/3/metadata/journals/`; the parent summary requires all 786 records for complete status. The wrapper stops after an incomplete segment and never merges different rules. Modes remain `none`; distance and room caps remain six and two.

Measured own seconds per read: camera displacement 7.252, rotation 4.749, direction 8.923, distance 25.509, and room 27.333. The supplied parity proof has 49 real distance G3T timings averaging 19.823 seconds and one room timing of 20.894 seconds. The synthetic tiny-test timing is excluded. Camera G3T cost uses the distance mean as an explicit estimate; the conservative calculation adds one G3T call per read. Room reads may activate it less often, and different generation trajectories may change decoding time.

Both distance reads need about 3.78 hours before staging/loading. Reserve one H100 for five hours, with the unchanged 1,800-second stop margin and 1,200-second return margin. Dollar price is **5 × the approved H100 hourly rate**, plus the separate CPU check. No rate was supplied or fetched. `TIME_PRICE.json` contains the arithmetic and assumptions.

## CPU rehearsal and limits

`LOCAL_REHEARSAL.json` records extraction into a fresh W2 root, every payload pin, step-544 admission, both settings/identities, all six worker argument sets, and tower socket rule selection with stub weights. The local rehearsal does not claim model restore or one real item per type.

Real CPU reads cannot run with the supplied assets. Missing runtime inputs include the 21.58-GB four-part step-544 export, the G3T archive, the environment/base/SAM/frame archive, selector assets, and the pinned runtime interpreter at their declared logical paths. `MISSING_RUNTIME.json` lists exact paths, byte counts, and hashes. W2 contains metadata and CPU fixtures; a real restore would exceed its 3-GB limit. The real-node CPU command authenticates staged production files and rehearses the wrapper before GPU submission.

The Orchard placement check requires explicitly typed H100 resources throughout `general`, because the unchanged submit helper requests generic `gpu:1`. It refuses an unproved placement. The operator checks for pending `jjy_*` jobs before submission.

## Pairing report

`tower_pair.py` uses this package's unchanged `h1eval.scorers.accuracy()` and room-bootstrap implementation. It reports own minus tower per camera type, distance under each rule, and room; per-call numeric errors and statuses; distance not-seen and other-status shares; capped reads; MRA on all units, metre questions, and reads without failed ground calls; and B1's stage-diagnostic table.

It pairs exact IDs and checks room/type, duplicate keys, rule/arm/export labels, journal identity consistency, and evaluator/reader code hashes. Missing keys remain explicit. A camera type meets the take-over bar only with complete paired coverage and a lower 95% bound above −5 points. Reads without any ground call are included in the explicitly documented no-failed-ground subset.

`selfcheck/TOWER_ARM_DEVS1.md` and `selfcheck/curve.json` compare H1-0 own with itself. Distance reproduces MRA 0.200, metre MRA 0.297674 on 43 questions, 63 not-seen reads, and 33 capped reads. These files are **self-check evidence, not tower results**. No empirical tower result or take-over claim exists yet.

## Reproduction

Run the builder only in a fresh package directory or with an explicit complete reader inventory if source bytes change: its production refresh deliberately freezes existing reader bytes. The delivered payload is already built and validated; do not refresh it merely to stage the kit.

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -B out/build_package.py
/scratch/jjyeung/envs/p1cpu/bin/python -B out/build_operator.py
/scratch/jjyeung/envs/p1cpu/bin/python -B out/build_delivery.py
```

`OPERATIONS_TOWER.md` gives prerequisites and interpretation for these exact operator commands. They have not executed:

```bash
set -euo pipefail
umask 077
: "${D:?Set D to the opaque delivery directory}"
P=/project/community/jjyeung/e47d0593fefec
printf '%s  %s\n' 1a60c9826f8d3d49081930e12dcf5434a3a876af805c2570585c7c29d4b98c03 "$D/1.tgz" | sha256sum -c -
mkdir -m 700 "$P"
tar -xzf "$D/1.tgz" -C "$P"
chmod 700 "$P/a"
cd "$P"
```

```bash
CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 05:00:00
```

```bash
env -i PATH=/usr/local/bin:/usr/bin:/bin HOME="$HOME" USER="$USER" \
  srun --account=mt01 --partition=general --nodes=1 --ntasks=1 \
  --job-name=a15_cot_ape47d0593fefecc \
  --cpus-per-task=16 --mem=200G --time=04:00:00 --export=ALL \
  /usr/bin/python3 -I -s -B "$P/a/5.py" --package "$P" \
  --sequence "$P/a/6.py" --results "$P/a/c"
```

```bash
sinfo -N -h -p general -o '%G' > "$P/a/7.txt"
/usr/bin/python3 -I -s -B - "$P/a/7.txt" <<'PY'
import re,sys
from pathlib import Path
rows=[s.strip() for s in Path(sys.argv[1]).read_text().splitlines() if s.strip()]
gpu=[g for row in rows for g in row.split(',') if g.startswith('gpu:')]
assert rows and gpu
assert all(re.fullmatch(r'gpu:[^:]*[Hh]100[^:]*:[0-9]+(?:\([^)]*\))?',g) for g in gpu)
PY
squeue -u "$USER" -h -o '%j %T' > "$P/a/9.txt"
/usr/bin/python3 -I -s -B - "$P/a/9.txt" <<'PY'
import sys
from pathlib import Path
rows=[s.split() for s in Path(sys.argv[1]).read_text().splitlines()]
assert not any(len(r)>=2 and r[0].startswith('jjy_') and r[1] in ('PENDING','PD') for r in rows), 'Pending priority job; stop'
PY
JOB_REPLY=$(/usr/bin/python3 -I -s -B 3.py submit --gpus 1 --time 05:00:00)
JOB=${JOB_REPLY%%;*}
[[ "$JOB" =~ ^[0-9]+$ ]]
printf '%s\n' "$JOB" > "$P/a/8.txt"
```

```bash
JOB=$(<"$P/a/8.txt")
RET=$(/usr/bin/python3 -I -s -B - "$JOB" <<'PY'
import sys
print('e47d0593fefec'+format(int(sys.argv[1]),'08x'))
PY
)
/usr/bin/python3 -I -s -B 3.py fetch --return-token "$RET" --out "$P/a/f"
```

```bash
cd /scratch/jjyeung/orch_n30/reader_r1/work/b1p
/scratch/jjyeung/envs/p1cpu/bin/python -B out/unpack_return.py \
  --archive work/f/0.tgz --exit work/f/EXIT.json --out work/ret
/scratch/jjyeung/envs/p1cpu/bin/python -B out/tower_pair.py \
  --package out/src \
  --own in/h10own/170631/items.jsonl in/h10own/170706/items.jsonl in/h10own/170694/items.jsonl \
  --tower-null work/ret/0 --tower-candidates work/ret/1 \
  --out out/tower_results
```

## Handoff

`REVIEW_REQUEST.md` scopes the requested cross-family review. The review must assess the default-equivalence proof, all three wiring paths, identity isolation, external batch wrapper, and the infeasible full-coverage estimate. The five-hour command is a distance-first partial-read budget, not a promise to finish all 786 items.

All successful task writes stay in W2. No SSH, Git, network, Slurm, GPU job, process kill, or deletion ran. W2 is below 3 GB. `REMOVAL_CANDIDATES.md` lists retained local fixtures without requesting deletion. Compatibility comparisons with bf94 and W1 identify validation baselines; no superseded design narrative is retained.
