# Orchard pose-only C1 kit (lane orchard_kit, 2026-11-09)

## Question
Can pose-only C1 arms train on Orchard H100s with C1-a's recipe, so that pose experiments need not wait for AWS GPUs? The recipe is a warm start from C1-a m800 on the A1 rows and frames, with the duplicate layout and the fla kernels.

## Answer
**Yes.** On 4 H100s, Orchard reproduces pose_sweep's AWS CTRL step for step. CTRL continues C1-a m800 on C1-a's rows from step 801, at world 8. The Orchard run used world 4 with pose x8 microsteps per rank, so the global batch stays 32 and the rows match. Steps 1 and 2 give a pose loss of 0.229 and 0.263 on both clusters. Over steps 1-19 the mean |diff| is 0.0006 and the max is 0.0015, which is bf16 noise. Both runs drew the same rows (pose_indices sha f57acf55, identical to C1-a and CTRL).

Throughput:
- Orchard world 4 runs at 17-20 s/step, against AWS CTRL's ~15 s/step at world 8 over steps 6-19 (10.5 s/step median over all 300 steps), so per-GPU throughput is about equal.
- Peak memory is 57 GiB per rank (AWS world 8: 40 GiB).
- A fresh node takes ~12 min to stage, because every input is re-verified by sha, then ~5 min to step 1.

## Kit
- **Trainer.** psmix `5d6ec3e` (Trinity `/scratch/jjyeung/orch_cd/orchard_kit/work/psmix`, branch orchard-ps-w4) is pose_sweep's B2 `4f96e60` plus world 4 for warm-started pose_only runs. World 4 uses mix pose x8; world 8 keeps today's recipe byte for byte. The row order matches world 8's at every step. A 4-rank gloo step, resume and export passes for CTRL and all pose arms.
- **Kit root.** Orchard `/home/jjyeung/okit/x/23595428` holds b/, k/, o/ logs, arm/ preps and a runs/ metrics mirror.
  - Build on Trinity with `work/mkkit_ps.py COMMIT 4` (local copy `work/okit_ps`).
  - After each arm's prep (`b/jp<arm>.sh`), bind it with `work/bind_arm.sh KEY`.
  - Train with `b/jt4L<arm>.sh` (advanced partition, 4.5 h, USR1 at 15 min before the limit).
- **Path emulation.** A bwrap namespace mounts node-local mirrors at the code-aws paths, so C1-a's pinned receipts resolve unchanged: A1 rows 6f27ae81, frames 6eb820a4, m800 385581e8, fla ebe69df8.
- **Inputs.** The Orchard cache `/project/community/jjyeung/distill/okit/in` holds GCS `q7/7822a58d/*`: 18 objects, 128.2 GB, client md5 equal to GCS md5. They were uploaded by AWS job 119696 through session URIs minted on Trinity, and the map is `work/up/map.json`. Venv, base model, art and bwrap come from `cp4tk_rt/kit`.
- **Outputs.** Job outputs go to node /tmp, and small files are mirrored to Orchard /home. Exports go to GCS `q8/<root>/<run>_m<step>.tar.partKK-of-04` in the AWS artifact format (carrier-c1-artifact-v1); restore them by concatenating the parts and extracting the tar.
- **Second kit.** A final-mode variant (root b56a2e3b, trainer okmix `a298304`) supports T0-style pose-only final runs. It adds gravity/scale branches and frame markers, so it is not the CTRL parity path. It is parked.

## Limits
- Orchard `/project/community` is 100% full, so the kit only reads from it. The full disk blocked jobs at 08:25Z.
- Checkpoints stay on node /tmp, so a run cannot resume across nodes. Each run must fit one 4.5 h leg, which holds about 600 CTRL-sized steps.
- Capacity is one advanced 4-GPU node per user at a time. The 8-GPU preempt queue was booked out to ~11-17.
- An export needs a GCS session URI minted on Trinity in advance, one per part. Sixty are minted for the root-23595428 run names.

