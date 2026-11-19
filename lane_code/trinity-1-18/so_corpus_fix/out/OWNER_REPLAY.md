# Published-read verification on trinity-3-30

These commands are prepared, not executed. Install patch 01 (and patch 02 for new-read wrapper use) and place this `out/` bundle on trinity-3-30 first. Run only after the owner schedules the local source reads under the cluster rules. Every output is a new scratch artifact; the published corpus is read-only.

Set `BUNDLE` to the copied `out/` directory and `TOOL` to the patched ingester. Choose a fresh `REPLAY` scratch directory. The following paths are examples to set once:

```bash
BUNDLE=/scratch/jjyeung/orch_n30/corpus/review4_bundle/out
TOOL=/scratch/jjyeung/orch_n30/corpus/tool/ingest_read.py
REPLAY=/scratch/jjyeung/orch_n30/corpus/review4_replay_20261119
```

The corpus owner on trinity-3-30 runs the cheap alias proof after scheduling shared I/O. This agent did not run it on `/data*`. Set `BUNDLE` as above, then run:

```bash
date -u
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -I -s -B "$BUNDLE/scripts/prove_kit_alias_ids.py" --corpus-root /data2/jjyeung/agent_project_data/distill_trace_corpus
```

The script opens only the six named kit read files with report sources. It reads them serially at at most 1 MiB/s in 64 KiB chunks, validates each read ID and item count, and scans every `item_id` for `devrows:`. INDEX records 46,023,532 compressed bytes and 16,353 items across these files; these are snapshot values, not fresh measurements. No INDEX, source archive, directory tree, or other published file is read by the script. The script writes nothing.

Exit 0 means all six files completed with zero matching IDs. Together with their recorded zero orphan counts, this rules out the actual-ID alias defect in finding 7. Exit 1 means matching IDs exist and source inspection is needed. Exit 2 means the proof is incomplete; missing/corrupt files, malformed rows, identity/count mismatches, and oversized rows cannot yield success. This scan does not certify duplicate report scores (finding 3) or any native-return check. Stop if a command is killed; do not relaunch automatically.

For each read, compare the two scratch read-file SHA256 values after both commands exit 0. A strict exit 2 is an unresolved integrity or partial-return refusal; inspect it before proceeding. Stop on unexpected termination and do not retry automatically. The indexed published SHA256 is also shown, but its publisher used a different tool version. A strict/default difference isolates the opt-in checks; a difference from publication alone does not.

## 17c4ffa4_s100_devS1R0facing_direct_a24ea1a1936

Published read SHA256: `8b4d78c2370489193683456ee573e0d7026a1cb00f1171f3a906dbef3cd39b89`.

```bash
date -u
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$TOOL" ingest --source /scratch/jjyeung/orch_n30/corpus/orchard_in/x/ae71c903_fetched/a24ea1a1936/result.tar.gz --meta "$BUNDLE/replay_meta/17c4ffa4_s100_devS1R0facing_direct_a24ea1a1936.json" --read-id 17c4ffa4_s100_devS1R0facing_direct_a24ea1a1936 --out "$REPLAY/default"
date -u
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$TOOL" ingest --source /scratch/jjyeung/orch_n30/corpus/orchard_in/x/ae71c903_fetched/a24ea1a1936/result.tar.gz --meta "$BUNDLE/replay_meta/17c4ffa4_s100_devS1R0facing_direct_a24ea1a1936.json" --read-id 17c4ffa4_s100_devS1R0facing_direct_a24ea1a1936 --out "$REPLAY/enabled" --review2-checks
nice -n 10 sha256sum "$REPLAY/default/reads/17c4ffa4_s100_devS1R0facing_direct_a24ea1a1936.jsonl.gz" "$REPLAY/enabled/reads/17c4ffa4_s100_devS1R0facing_direct_a24ea1a1936.jsonl.gz"
```

If the verified strict output must become a new read, this exact command uses a new ID. It stages only; publication remains a separate owner action:

```bash
date -u
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$TOOL" ingest --source /scratch/jjyeung/orch_n30/corpus/orchard_in/x/ae71c903_fetched/a24ea1a1936/result.tar.gz --meta "$BUNDLE/replay_meta/17c4ffa4_s100_devS1R0facing_direct_a24ea1a1936.json" --read-id 17c4ffa4_s100_devS1R0facing_direct_a24ea1a1936.review4 --out "$REPLAY/new_ids" --review2-checks
```

## 359fcc3c_s100_devS1R0facing_direct_af35386aa3e

Published read SHA256: `0c0ada991f36936e25e4e6d384f5cc3c5991b6a9fd946327191d1f3681f68dba`.

```bash
date -u
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$TOOL" ingest --source /scratch/jjyeung/orch_n30/corpus/orchard_in/x/ae71c903_fetched/af35386aa3e/result.tar.gz --meta "$BUNDLE/replay_meta/359fcc3c_s100_devS1R0facing_direct_af35386aa3e.json" --read-id 359fcc3c_s100_devS1R0facing_direct_af35386aa3e --out "$REPLAY/default"
date -u
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$TOOL" ingest --source /scratch/jjyeung/orch_n30/corpus/orchard_in/x/ae71c903_fetched/af35386aa3e/result.tar.gz --meta "$BUNDLE/replay_meta/359fcc3c_s100_devS1R0facing_direct_af35386aa3e.json" --read-id 359fcc3c_s100_devS1R0facing_direct_af35386aa3e --out "$REPLAY/enabled" --review2-checks
nice -n 10 sha256sum "$REPLAY/default/reads/359fcc3c_s100_devS1R0facing_direct_af35386aa3e.jsonl.gz" "$REPLAY/enabled/reads/359fcc3c_s100_devS1R0facing_direct_af35386aa3e.jsonl.gz"
```

If the verified strict output must become a new read, this exact command uses a new ID. It stages only; publication remains a separate owner action:

```bash
date -u
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$TOOL" ingest --source /scratch/jjyeung/orch_n30/corpus/orchard_in/x/ae71c903_fetched/af35386aa3e/result.tar.gz --meta "$BUNDLE/replay_meta/359fcc3c_s100_devS1R0facing_direct_af35386aa3e.json" --read-id 359fcc3c_s100_devS1R0facing_direct_af35386aa3e.review4 --out "$REPLAY/new_ids" --review2-checks
```

## 359fcc3c_s200_devS1facing_direct_a4cadd8934b

Published read SHA256: `8050162e7dba911346a3438e37bdccb90dba10b8160680f1065c6a26cbc1ca55`.

```bash
date -u
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$TOOL" ingest --source /scratch/jjyeung/orch_n30/cont_ops16/work/c15/h1read/readk/kit/build/a4cadd8934b/fetched/result.tar.gz --meta "$BUNDLE/replay_meta/359fcc3c_s200_devS1facing_direct_a4cadd8934b.json" --read-id 359fcc3c_s200_devS1facing_direct_a4cadd8934b --out "$REPLAY/default"
date -u
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$TOOL" ingest --source /scratch/jjyeung/orch_n30/cont_ops16/work/c15/h1read/readk/kit/build/a4cadd8934b/fetched/result.tar.gz --meta "$BUNDLE/replay_meta/359fcc3c_s200_devS1facing_direct_a4cadd8934b.json" --read-id 359fcc3c_s200_devS1facing_direct_a4cadd8934b --out "$REPLAY/enabled" --review2-checks
nice -n 10 sha256sum "$REPLAY/default/reads/359fcc3c_s200_devS1facing_direct_a4cadd8934b.jsonl.gz" "$REPLAY/enabled/reads/359fcc3c_s200_devS1facing_direct_a4cadd8934b.jsonl.gz"
```

If the verified strict output must become a new read, this exact command uses a new ID. It stages only; publication remains a separate owner action:

```bash
date -u
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$TOOL" ingest --source /scratch/jjyeung/orch_n30/cont_ops16/work/c15/h1read/readk/kit/build/a4cadd8934b/fetched/result.tar.gz --meta "$BUNDLE/replay_meta/359fcc3c_s200_devS1facing_direct_a4cadd8934b.json" --read-id 359fcc3c_s200_devS1facing_direct_a4cadd8934b.review4 --out "$REPLAY/new_ids" --review2-checks
```

## 469ddece_s544_devS1_native_b07a20b364

Published read SHA256: `960694a402e26b2d698e0e205d3df6d2a8638ad4a461ef48f2e948a6e8761a33`.

```bash
date -u
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$TOOL" ingest --source /scratch/jjyeung/orch_n30/b04_e2ehook/work/n13/full_c8r/result.tar.gz --meta "$BUNDLE/replay_meta/469ddece_s544_devS1_native_b07a20b364.json" --inputs /scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/A4/src --read-id 469ddece_s544_devS1_native_b07a20b364 --out "$REPLAY/default"
date -u
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$TOOL" ingest --source /scratch/jjyeung/orch_n30/b04_e2ehook/work/n13/full_c8r/result.tar.gz --meta "$BUNDLE/replay_meta/469ddece_s544_devS1_native_b07a20b364.json" --inputs /scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/A4/src --read-id 469ddece_s544_devS1_native_b07a20b364 --out "$REPLAY/enabled" --review2-checks
nice -n 10 sha256sum "$REPLAY/default/reads/469ddece_s544_devS1_native_b07a20b364.jsonl.gz" "$REPLAY/enabled/reads/469ddece_s544_devS1_native_b07a20b364.jsonl.gz"
```

If the verified strict output must become a new read, this exact command uses a new ID. It stages only; publication remains a separate owner action:

```bash
date -u
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$TOOL" ingest --source /scratch/jjyeung/orch_n30/b04_e2ehook/work/n13/full_c8r/result.tar.gz --meta "$BUNDLE/replay_meta/469ddece_s544_devS1_native_b07a20b364.json" --inputs /scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/A4/src --read-id 469ddece_s544_devS1_native_b07a20b364.review4 --out "$REPLAY/new_ids" --review2-checks
```

## 673bc60f_s100_devS1R0_direct_a5d2d909067

Published read SHA256: `13bdd0fb95b4765262c9113735a8a4ca7695ac434845a1f091eea9a72bc7ec35`.

```bash
date -u
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$TOOL" ingest --source /scratch/jjyeung/orch_n30/cont_ops16/work/c15/h1read/kit/build/a5d2d909067/fetched/result.tar.gz --meta "$BUNDLE/replay_meta/673bc60f_s100_devS1R0_direct_a5d2d909067.json" --read-id 673bc60f_s100_devS1R0_direct_a5d2d909067 --out "$REPLAY/default"
date -u
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$TOOL" ingest --source /scratch/jjyeung/orch_n30/cont_ops16/work/c15/h1read/kit/build/a5d2d909067/fetched/result.tar.gz --meta "$BUNDLE/replay_meta/673bc60f_s100_devS1R0_direct_a5d2d909067.json" --read-id 673bc60f_s100_devS1R0_direct_a5d2d909067 --out "$REPLAY/enabled" --review2-checks
nice -n 10 sha256sum "$REPLAY/default/reads/673bc60f_s100_devS1R0_direct_a5d2d909067.jsonl.gz" "$REPLAY/enabled/reads/673bc60f_s100_devS1R0_direct_a5d2d909067.jsonl.gz"
```

If the verified strict output must become a new read, this exact command uses a new ID. It stages only; publication remains a separate owner action:

```bash
date -u
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$TOOL" ingest --source /scratch/jjyeung/orch_n30/cont_ops16/work/c15/h1read/kit/build/a5d2d909067/fetched/result.tar.gz --meta "$BUNDLE/replay_meta/673bc60f_s100_devS1R0_direct_a5d2d909067.json" --read-id 673bc60f_s100_devS1R0_direct_a5d2d909067.review4 --out "$REPLAY/new_ids" --review2-checks
```

## 673bc60f_s200_devS1R0_direct_a8102c3207b

Published read SHA256: `6adf517be14f060f469b2815414373bdde738d3c64714c1371973eeef6710ed7`.

```bash
date -u
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$TOOL" ingest --source /scratch/jjyeung/orch_n30/cont_ops16/work/c15/h1read/kit/build/a8102c3207b/fetched/result.tar.gz --meta "$BUNDLE/replay_meta/673bc60f_s200_devS1R0_direct_a8102c3207b.json" --read-id 673bc60f_s200_devS1R0_direct_a8102c3207b --out "$REPLAY/default"
date -u
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$TOOL" ingest --source /scratch/jjyeung/orch_n30/cont_ops16/work/c15/h1read/kit/build/a8102c3207b/fetched/result.tar.gz --meta "$BUNDLE/replay_meta/673bc60f_s200_devS1R0_direct_a8102c3207b.json" --read-id 673bc60f_s200_devS1R0_direct_a8102c3207b --out "$REPLAY/enabled" --review2-checks
nice -n 10 sha256sum "$REPLAY/default/reads/673bc60f_s200_devS1R0_direct_a8102c3207b.jsonl.gz" "$REPLAY/enabled/reads/673bc60f_s200_devS1R0_direct_a8102c3207b.jsonl.gz"
```

If the verified strict output must become a new read, this exact command uses a new ID. It stages only; publication remains a separate owner action:

```bash
date -u
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$TOOL" ingest --source /scratch/jjyeung/orch_n30/cont_ops16/work/c15/h1read/kit/build/a8102c3207b/fetched/result.tar.gz --meta "$BUNDLE/replay_meta/673bc60f_s200_devS1R0_direct_a8102c3207b.json" --read-id 673bc60f_s200_devS1R0_direct_a8102c3207b.review4 --out "$REPLAY/new_ids" --review2-checks
```

## 673bc60f_s200_facing_direct_a2e46c0504e

Published read SHA256: `dfb9e3f3aea3739834c4281d619d694e0f40161f608e0d0f386b067c068445a2`.

```bash
date -u
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$TOOL" ingest --source /scratch/jjyeung/orch_n30/cont_ops16/work/c15/h1face/kit/build/a2e46c0504e/fetched/result.tar.gz --meta "$BUNDLE/replay_meta/673bc60f_s200_facing_direct_a2e46c0504e.json" --read-id 673bc60f_s200_facing_direct_a2e46c0504e --out "$REPLAY/default"
date -u
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$TOOL" ingest --source /scratch/jjyeung/orch_n30/cont_ops16/work/c15/h1face/kit/build/a2e46c0504e/fetched/result.tar.gz --meta "$BUNDLE/replay_meta/673bc60f_s200_facing_direct_a2e46c0504e.json" --read-id 673bc60f_s200_facing_direct_a2e46c0504e --out "$REPLAY/enabled" --review2-checks
nice -n 10 sha256sum "$REPLAY/default/reads/673bc60f_s200_facing_direct_a2e46c0504e.jsonl.gz" "$REPLAY/enabled/reads/673bc60f_s200_facing_direct_a2e46c0504e.jsonl.gz"
```

If the verified strict output must become a new read, this exact command uses a new ID. It stages only; publication remains a separate owner action:

```bash
date -u
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$TOOL" ingest --source /scratch/jjyeung/orch_n30/cont_ops16/work/c15/h1face/kit/build/a2e46c0504e/fetched/result.tar.gz --meta "$BUNDLE/replay_meta/673bc60f_s200_facing_direct_a2e46c0504e.json" --read-id 673bc60f_s200_facing_direct_a2e46c0504e.review4 --out "$REPLAY/new_ids" --review2-checks
```
