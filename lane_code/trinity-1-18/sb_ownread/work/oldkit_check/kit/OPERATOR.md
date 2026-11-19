# Operator note: tower-and-own camera read at step 400 or 600

One Orchard job reads the 450 dev-S1 camera items (150 per type) with the tower arm and the own arm from the same export, so `ownread.py` can pair own minus tower by item. The tower arm keeps A4's settings byte for byte; only the operator `a/6.py`, the token and the export pin differ from A4.

## Submission settings

| Setting | Value |
|---|---|
| GPU job | `3.py submit --gpus 1 --time 05:00:00`: `sbatch --account=mt01 --partition=general --gres=gpu:1 --cpus-per-task=16 --mem=200G --time=05:00:00 --signal=B:USR1@1800 --no-requeue --job-name=a15_cot_ap<token>` |
| CPU check | `o_cpucheck.sh`: preempt, 8 CPUs, 200G, 04:00:00, no GPU |
| Card | one H100 80GB; `unpack_return.py` refuses any return with more than one card |
| Expected wall time | 2.1 h (upper 3.1 h if decoding runs 1.5x slower); reads stop being admitted at 4.5 h |
| GPU-hours | about 2.1 used, 5.0 reserved |

`kit/TIME_ESTIMATE.json` derives the estimate. Staging takes 257 s (A4). Each of the three per-type processes loads the tower (75 s) and the own arm (overhead up to 113 s, load included). Tower decoding took 3553 s at step 200 and 3448 s at step 544; own decoding took 3139 s at step 544 (job 170631, mode none). A 120 s return completes the total.

## What to pin at the milestone

The export's completion receipt `/project/community/jjyeung/okh7/x_69d2930d/o/gcs_673bc60f_m<step>.done` holds three fields: object, bytes and sha256. Write them into a pin file:

```json
{"step": 400, "member_directory": "m400",
 "object": "<field 1, q8/<hex8>/673bc60f_m400.tar>", "archive_bytes": <field 2>, "archive_sha256": "<field 3>",
 "done": "/project/community/jjyeung/okh7/x_69d2930d/o/gcs_673bc60f_m400.done",
 "part_bytes": <bytes of part00, optional; enables o_pullfill_resume.sh>}
```

The builder rewrites `9.json` `export_binding` (step, member directory, object) and the three `REVIEWED_*` constants of the fill helper `a/4.py`. It then reseals every hash. The fill on Orchard fails closed in three cases:
- the export does not have exactly four parts `<object>.part0{0..3}-of-04`;
- the artifact step, config hash, base identity or frame layout differs;
- run 673bc60f's preparation files (config, s1 receipt, data receipt) differ.

If the run or its preparation changed, add `run`, `config_sha256`, `base_identity`, `frame_layout` or `preparation_sha256` to the pin. The receipt path and the `q8/` object prefix follow step 200's pattern; confirm them against the real receipt.

## Build and check (Trinity, CPU, seconds)

```bash
K=<kit>; PY=/scratch/jjyeung/envs/p1cpu/bin/python   # Python 3.12 with numpy and pytest
$PY $K/build_ownread.py --out <builds>/r400 --export-pin pin400.json
$PY $K/tests/check_build.py <builds>/r400
```

The builder refuses to run unless resealing A4 reproduces A4's `1.tgz` byte for byte. It appends the fresh token to `<builds>/TOKEN_LEDGER.jsonl`; copy that line into the Orchard job ledger. `check_build.py` checks the seals and the diff against A4, runs `bash -n` on the scripts and compiles every Orchard helper under `/usr/bin/python3` 3.6.

## Orchard sequence (unchanged from A4)

1. Copy `<build>/1.tgz` into an opaque staging directory `D=/project/community/jjyeung/okh7/a15_cot_ap<other hex>`. `D` must differ from the package directory `P=…/a15_cot_ap<token>`, which the scripts hard-code.
2. `D=$D bash o_place.sh` checks the 1.tgz checksum and requires that `P` does not exist yet. It then extracts into `P` and verifies every file hash, every pin and the binding's step.
3. `bash o_pullfill.sh` runs in the background. It pulls the four parts (about 21.6 GB), fills `a/1.json` and `a/export.json`, and runs `3.py check`. Use `o_pullfill_resume.sh` only when part 0 finished and parts 1–3 are absent.
4. `bash o_cpucheck.sh` submits the CPU check. Its rehearsal checks the per-type worker arguments and runs the tower socket and the own head server on stubs.
5. `bash o_sub.sh` verifies the CPU receipt, requires an empty `jjyeung` general queue and a return pool under 75 MB, then submits.
6. When the job ends, `bash o_fetch.sh` fetches the return into `a/f`; copy `a/f` to Trinity by A4's route.

## Score (Trinity)

```bash
$PY <build>/unpack_return.py --archive f/0.tgz --exit f/EXIT.json --out <builds>/ret400 --return-token <token><job as 8 hex>
$PY $K/ownread.py --root <builds>/ret400 --out <builds>/score400
```

`ownread.txt` lists own, tower and own minus tower for each camera type, with 95% and 99.29% room-bootstrap intervals (`score_r5.bootstrap`). It flags two bars: point at least −5 pp, and 95% lower bound above −5 pp. Use the interval bar to drop G3T and treat the point bar as the weaker signal. The file also prints deltas against the registered step-544 figures (marked "unpaired reference"), deltas paired by item against the step-544 rows, and deltas paired by item against A4's step-200 tower return. The scorer refuses a return whose tower settings, reader, evaluator, maker or parity hashes differ from A4's.

## GO this needs

- The main orchestrator's or the user's GO for one Orchard H100 job (about 2.1 GPU-h used, 5 reserved), given once the step-400 or step-600 receipt exists.
- One independent review of the fork: the operator diff (`OPERATOR_DIFF_VS_A4.patch`) and `ownread.py`, because the read decides whether G3T stays.
- Do not launch the step-200 proof build; it exists to prove the kit.

## Differences from A4 (recorded)

- Workers run one process per camera type instead of A4's single worker, so G3T memo hits stay within a type. The memo holds frozen-module values, so outputs do not change; timings do.
- The own arm runs mode none only. H1-0 also ran intervention modes.
- The step-544 own rows came from older reader, evaluator, maker and parity code (H1-0 kit). Own-versus-own544 deltas therefore mix a step change with a code change; the in-read own-minus-tower pairing does not.
- The registered step-544 intervals used `h1eval.statistics.bootstrap` (seed 20261115). `ownread.py` prints that interval as "544-RNG" next to `score_r5.bootstrap`.
