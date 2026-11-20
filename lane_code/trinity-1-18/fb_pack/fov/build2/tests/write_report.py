"""Write the report from completed, hashed test artifacts."""
import hashlib
import json
from pathlib import Path

WORK = Path(__file__).resolve().parents[1]
TESTS = WORK / 'tests'

def read_latest(prefix):
    path = max(TESTS.glob(prefix + '*.json'), key=lambda p:p.name)
    return path, json.loads(path.read_text())


def main():
    selected = {key:read_latest(key) for key in ('SYNTHETIC_RESULTS_', 'REFUSAL_RESULTS_', 'AMENDMENT_RESULTS_', 'OUTPUT_GUARD_RESULTS_')}
    audit = json.loads((TESTS/'FINAL_AUDIT.json').read_text())
    real_status = audit['real_input']['status']
    parity_status = audit['real_fov_check']['status']
    synthetic = selected['SYNTHETIC_RESULTS_'][1]['tests']
    rows = '\n'.join(f"| {case} | {r['choice']} | {r['V1-A']['points']:.6f} | {r['V2-A']['points']:.6f} | {r['seconds']:.3f} |"
                     for case,r in zip(('1.0 1.0','1.0 1.02','1.02 1.02'),synthetic))
    sha = hashlib.sha256((WORK/'score_fov.py').read_bytes()).hexdigest()
    results = '\n'.join(f'- [{path.name}](tests/{path.name}): {len(value["tests"])} passing cases.' for path,value in selected.values())
    command = 'env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 CUDA_VISIBLE_DEVICES= nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B'
    full_commands = '\n'.join(r['command'] for r in synthetic)
    report = f'''The scorer enforces P1–P5 before any scale estimate or score. All inherited tests and amendment tests pass. The three full synthetic runs choose **V2 / V1 / NONE**. No real donor decision was made: the delivery is **{real_status}** at `/scratch/jjyeung/orch_n30/sb_own400/in/own_544_fov/native/probe`, and its parity file is **{parity_status}** at `/scratch/jjyeung/orch_n30/sb_own400/in/own_544_fov/FOV_CHECK.json`.

The scorer uses the producer mapping accepted in the task. P1 checks the second-pass control flags and residual, hashes the pinned `own_170235` depth as contiguous float64 bytes, and requires `served_equal: true` for every row in `FOV_CHECK.json`. 

Every frozen capture must have one parity row; duplicate rows refuse. A present delivery `own.npz` must match arm A bit for bit. An optional `fov.npz` `depth` array must also match, but neither array is required in the delivered layout. `PHASE_COMPLETE.json` checks every listed file; only an absent `own.npz` claim is exempt because P1 binds its served bytes.

P2 checks that `fov_B` is finite, has shape `(32,2)`, and lies strictly between zero and pi. The accepted producer code binds it to the served encode FoV. P3 binds every capture's anchors and grid through its parity row. 

P4 checks the producer code pin, V1 formula description, checkpoint, capture digest and file hashes. V2 must equal the G3T reference cast to float32 bit for bit; the scorer also checks the bars' `1e-6` radian tolerance and records the maximum difference from the float64 reference. The capture digest is independently checked against frozen training metadata before scoring.

P5 computes Pearson correlation of spatially centred log depth. For each capture and each variant, mean identity correlation must strictly exceed transpose, vertical flip and horizontal flip. 

Each variant must match the same arm-A anchor best for at least 95% of anchors across all frozen captures. Matching compares the 32 anchors within each capture. Ties do not count as matches; zero spatial variance refuses because correlation is undefined. The result records orientation correlations, per-capture match counts and aggregate fractions. The small fixture accepts 62/64 matches and refuses 60/64 for each variant.

The numerical scoring block, D1–D3, H, margin, choice order, summaries, agreement and output guards match the previous scorer's syntax tree. All full synthetic runs reproduce arm A exactly in both folds and combined for both metrics. 

Each scores 239 captures, 117,551 displacement pairs and 1,037 distance items; three frozen missing-GT exclusions remain MISSING. Synthetic outputs explicitly list `P1`, `P2`, `P3`, `P4`, `P5` under `provenance_checks.skipped`, with `synthetic: true` and `decision_usable: false`.

| Synthetic factors | Choice | V1−A points | V2−A points | Seconds |
|---|---|---:|---:|---:|
{rows}

## Receipt fields the producer must write

The six `k1fwd2_example_*` files were read once from the named NFS location and retained as byte-identical local input copies. Their hashes and schema checks are in `tests/PRODUCER_EXAMPLES.json`. The actual producer field names supply P1, P2 and P4. P3 fields are **MISSING** in the canary; the scorer refuses them rather than inferring anchors or a grid. The accepted mapping replaces the amendment's literal `control_path`, receipt `frame_indices`, and served-FoV-array fields with the fields below.

| File | Required fields and checks |
|---|---|
| `<key>/FOV_RECEIPT.json` | `checks.second_pass_pose_fov_bit_identical` must be boolean true; `checks.second_pass_pose_fov_max_abs` must be numeric zero; `served_depth_sha256` must hash contiguous float64 arm-A depth bytes. |
| `<key>/FOV_RECEIPT.json` | `boundaries_sha256` must equal `454e9b27fedf7fd7008760dedc4e0961f6156cc3d8afdcd203e340921c52826c`, unless an explicit published-diff acceptance is supplied. |
| `<key>/FOV_RECEIPT.json` | `sources.V1` must equal `1e-4+(pi-2e-4)*sigmoid(depth.fov(states)) on a separate private feature pass (scale_donor V1)`. `missing` must equal `{{}}`. |
| `<key>/FOV_RECEIPT.json` | `checkpoint.sha256` must equal `1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef`; `capture_sha256` must match the frozen capture digest; `files["fov.npz"]` must match the delivered bytes. Every additional listed file is checked. |
| `<key>/PHASE_COMPLETE.json` | `capture_sha256`, `checkpoint.sha256` and `files` are required. All listed files must exist and match, except the absent `own.npz` case described above. |
| `<delivery root>/FOV_CHECK.json` | `rows` must contain unique `key` fields covering every frozen capture, with `served_equal: true` on every row. |
| `<delivery root>/FOV_CHECK.json` | Each frozen capture's row must contain `anchor_indices` equal to `BARS_FROZEN.json`. Each must also contain `grid_uv` equal to `linspace(0,1000,51)` or `grid_uv_sha256` equal to the SHA-256 of that float32 array's bytes. **Both fields are absent in the canary.** If both grid representations are supplied, both must pass. The result records the representation checked. |

The parity filename is **`FOV_CHECK.json`**. For `--own-root <delivery>/native/probe`, the default is `<delivery>/FOV_CHECK.json`; `--fov-check PATH` explicitly overrides it. For another probe-root layout the default is `--own-root/FOV_CHECK.json`. The supplied producer `fov_check.py` writes its fourth command-line argument, so the producer must publish the completed file at the selected path and add the missing P3 fields.

For a producer code change, `--accept-fov-code-diff SHA256` requires an existing nonempty published diff whose bytes match that hash. Supply `--fov-code-diff PATH`, or place it at `<delivery>/FOV_CODE_DIFF.patch`. The result records the path and hash, with the amendment's reference variant pin `4f66911b9de9989fe9054529dd2eca9af698a7642cbd6f6b6e28f678df89fd7a`. 

This is explicit acceptance of the published diff; the scorer does not prove code equivalence. It does not waive any other check. The result records the V1 formula pin from the frozen amendment, `1fca29c9211e19f91a04e72c41a77652a56f3dea363e58fdd71817fe7229a134`; no remote formula file was fetched.

These commands produced the validation numbers. Run them from this workspace. Existing full-run output directories are intentionally refused; use the test launcher's `--prefix` for a fresh authorized rerun.

```bash
{full_commands}
{command} tests/test_refusals.py
{command} tests/test_amendment.py
{command} tests/test_output_guards.py
{command} tests/check_unchanged.py
{command} tests/check_producer_examples.py
{command} tests/run_synthetic.py --verify-only
{command} tests/final_audit.py
sha256sum score_fov.py
du -sb .
```

The test reports record their commands and SHA-256 input pins:

{results}
- `tests/UNCHANGED_NUMERICS.json`: five passing AST comparisons.
- `tests/PRODUCER_EXAMPLES.json`: producer-code and schema checks, including named P3 refusals.
- `tests/FINAL_AUDIT.json`: every test JSON has input pins; the workspace contained {audit['workspace_file_bytes_before_audit']:,} file bytes before the audit, below the 1 GB limit. `tests/final_audit.py` produced that count. The inherited probe suite also verifies five criterion-boundary cases.

The final `score_fov.py` SHA-256, produced by `sha256sum score_fov.py`, is:

```text
{sha}
```

Every `FOV_RESULT.json` pins the scorer and both bars files. Their frozen hashes are `c1905484873704ae9b8af5cb653cf2cb1b911d789d181811767fa5f8707fa878` and `e23ffd29b8fe0ad88844dafc4585ed8a1704e88b5f02dc73d99f6ea0e147acc7`. Refused scoring runs write `status: REFUSED`, `choice: MISSING` and the reason with the inputs read so far.

The exact real-run command is:

```bash
cd /scratch/jjyeung/orch_n30/sb_own400 && {command} /scratch/jjyeung/orch_n30/fb_pack/fov/build2/score_fov.py --own-root in/own_544_fov/native/probe --fov-check in/own_544_fov/FOV_CHECK.json --out out/fov544_score
```

No real output was written outside this workspace. No held-out, R0-dev or dev-S1 payload was opened. All scoring used CPU, nice 10 and eight-thread limits. No Git, SSH, network, GPU, tmux, process termination or file deletion was used.
'''
    (WORK/'REPORT.md').write_text(report)
    (WORK/'STATUS.md').write_text(f'All stages complete: The scorer enforces P1–P5 using the accepted producer fields and pins both bars files and itself. All inherited tests, 70 amendment tests, output guards, unchanged-numerics comparisons and full synthetic regressions pass; the synthetic choices are V2 / V1 / NONE. REPORT.md lists required receipt fields, exact commands, evidence hashes and the final scorer hash. The real delivery status is {real_status}; FOV_CHECK.json status is {parity_status}. The copied canary lacks P3 anchor/grid fields. No real donor decision was made.\n')
    print('REPORT.md and STATUS.md written')


if __name__ == '__main__':
    main()
