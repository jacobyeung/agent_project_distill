The kit is ready for the authorized lane at `/project/community/jjyeung/ae63d9b7124fc`; job names are `a15_cot_apae63d9b7124fc`. Orchard execution remains untested. `orchard_tower2x_b` is unchanged.

The recipe remains OpenCV bicubic (`INTER_CUBIC`), Up/Down unrotated, Left clockwise, then 2.5× resize. Each frame returns its raw RGB SHA256, a Boolean comparison with the Trinity hash, and cv2/PIL/numpy versions. Each arm and the whole return count matches; the full run has 950 frame observations, including repeated anchors. PNG SHA256, dimensions and binding checks remain fatal.

A′ uses 32 anchors and B uses 63 frames for all ten captures. A′–T1 relative-rotation RMS must be ≤1.0° on ≥8/10 captures. The scorer preserves rigid/similarity fits, all 496 anchor pairs, scale B/A′, gravity, and the coverage verdict. B confirms with ≥4/5 gross exits, ≥50% median reduction and no reference rise >2°; it refutes with ≤1/5 exits and <20% reduction. Missing comparisons remain incomplete; failed decode controls void the verdict. Only decode-record validation and reporting change in this kit's scorer.

Both CPU and GPU submissions request **200 GB**, eight CPUs and 30 minutes; the GPU job requests one H100. They retain the empty-general-queue guard, excluded node and no-requeue setting. The forecast is **1461.344494 s = 24.355742 min**: `600 + 78.209813467 + 1.5 × 10 × (17.931165216 + 22.277813484) + 60 + 120`. Staging and GPU runtime remain unmeasured for this kit.

Placement adds **306,813 file-content bytes**. The single `o_place.sh` transport is **95,101 bytes**, below 1 MB. It authenticates the six small files and verifies the existing **44,374,984-byte** archive before creating a hard link from `/project/community/jjyeung/ac794e028b16f/8.tgz`; it copies no frame bytes. Archive SHA256: `e8072d952b78f6eb3317d8214821ded02cebfa9a4349e81f317961fd146813ff`. The runtime verifies it again before staging. Existing destinations, missing sources and wrong hashes fail without retries.

CPU errors go to `4.err`, GPU errors to `5.err`, and submission preflight errors to `6.err`, each capped at 16 KiB. Records contain exception type, E-code and at most 32 file:line entries without messages or source text. Kit filenames remain numeric; other filenames use SHA256 aliases, with no payload directories. Unknown exception type names use hex encoding. Slurm saves `4.out`/`4.stderr` and `5.out`/`5.stderr` inside the token directory. The supervisor repeats error records on stderr and summarizes arbitrary payload streams by byte count/SHA256 to prevent opaque-word or path leaks. Fetch includes the logs.

The real-capture CPU test passes on **41069054**, both 32/63-frame arms, through actual preprocessing and pose conversion with a stub tower. OpenCV matches **95/95** raw hashes. A test-only Pillow bicubic replacement matches **0/95** and still completes both arms; production recipe configuration stays unchanged. Wrong PNG hashes fail with **E07**. The test takes **27.54 s** and peaks at **1,544,240 KiB RSS**, within the local 20 GB limit. This is synthetic camera evidence, not a coverage result.

All **26 scorer/scheduling tests pass**, including the 21 existing tests and five decode-record tests. Drift leaves the camera metrics, controls and verdict unchanged; false match flags, malformed hashes/versions, wrong counts and PNG bindings are rejected. The scorer CLI accepts the authenticated mismatch return and labels it synthetic. Installer tests confirm the same inode and byte-identical small files, and reject existing destinations, missing sources, wrong archive hashes and corrupt transport authentication. CPU/GPU exception tests and a real supervisor subprocess retain sanitized traces.

The opaque-word scan passes **131 checks** across shipped sources, decoded transport members, lane scripts, diagnostic types/codes and actual error/stdout/stderr fixtures. The unchanged archive hash binds K3c's full 630-PNG scan. Exceptions remain inherited configuration values, the required excluded-node literal and compressed transport bytes whose decoded members are checked. Shell syntax and shipped Python compilation pass.

Run on the authorized lane from `gbuild`, in order. Wait for CPU success before submit, and GPU completion before fetch; check status at most once a minute. The installer should print `306813`.

```bash
cd /scratch/jjyeung/orch_n30/cont_ops24_c/gbuild
set -euo pipefail
sha256sum --check --quiet orchard_tower2x_c/SHA256SUMS_K3D
ssh orchard 'bash -s' < orchard_tower2x_c/o_place.sh
ssh orchard 'bash -s' < orchard_tower2x_c/o_cpu.sh
# Wait for the CPU check to pass.
ssh orchard 'bash -s' < orchard_tower2x_c/o_check_sub.sh
# Wait for the GPU job to finish.
mkdir -p orchard_tower2x_c/returned
ssh orchard 'bash -s' < orchard_tower2x_c/o_fetch.sh | pv -q -L 8000000 > orchard_tower2x_c/returned/return.tgz
tar -xzf orchard_tower2x_c/returned/return.tgz -C orchard_tower2x_c/returned
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -B orchard_tower2x_c/score.py --return orchard_tower2x_c/returned/5.json --receipt orchard_tower2x_c/returned/5.1.json --reference orchard_tower2x_c/REFERENCE.json --out orchard_tower2x_c/returned/scored
```

`SHA256SUMS_K3D` binds the kit, report, tests, evidence, scorer/reference and reused archive. This delivery ran no SSH, Git, GPU, network, deletion, remote placement or submission. All writes stayed in `orchard_tower2x_c`. The report retains no revision-history sentences.
