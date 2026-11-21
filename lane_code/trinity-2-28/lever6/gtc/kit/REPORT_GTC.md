# GTC kit: SAM 3 tracker masks on rank 1's 46 captures, relifted inside dump 174135 (lever6; ORCH RULING 2026-11-21T19:39Z A)
## Frames
All 46 eligible captures (117 items: 18 ARKit, 28 ScanNet/ScanNet++ captures) have their 32 served anchors on trinity-2-28:
- 1,472 PNGs, 396,791,330 B: 832 in /scratch/jjyeung/devs1_frames and 640 in /scratch/jjyeung/orch_n30/nvkey1/work/c0stage/devs1_frames (lever5/k5/work/f also holds all of them).
- Every PNG's sha256 matches, and frame_binding_sha256 reproduces for all 150 items and equals the dump's.
- No stream is needed. Dense 64-frame sets exist too, but the kit tracks the 32 anchors.
## Arms as built
- t: seeded with the GT instance on its first anchor of at least --t-min-pixels (default 1) and carried forward only. 169 units cover 233 of 234 operands; one operand's GT appears on no anchor. Seed sizes at 1 px: 20 of 169 are under 50 px, 45 under 200 px, and the smallest is 1 px.
- s: K1's S_A0 rule, the served mask on the deployed lift's best frame (largest area among frames with lifted points; ties go to the lowest). It propagates forward and backward, as on K1. 165 units; 9 operands have no seed (2 lack a served object, 7 are unseen by the lift).
- Resize: seeds go up to 480x640 with the served path's own resize (nearest). Tracker output is resized to the canvas and then sampled [::2,::2]. The round trip is exact for all 334 seeds.
- Carry (K1's rule): the seed anchor keeps the seed; another anchor carries where the object score is above 0, and every other anchor is empty.
## GPU job
- Forecast: 379 s for both arms (t 179, s 191, load 9) or 188 s for t alone. Peak memory is at most K1's 5.29 GiB allocated (64 frames).
- Launch in tmux on trinity-2-28: `bash kit/launch_gpu.sh` (or `... t`). It checks SHA256SUMS_GTC, takes two nvidia-smi readings 300 s apart, and runs vnice.sh around the SAM 3 env under timeout 3600.
## Reading (CPU, about 10 min)
- Command: `relift_t.py --tracks ../out/track --out ../out/RELIFT_GTC.json`. It prints only "complete".
- The depth receipt is returned/4.json (the receipt for 0.gz; RETURN_RECEIPT.json has no verified field), as lever5's run used.
- Bootstrap draws with e - a = 0 leave the share undefined; they are dropped and counted. GT instance id 0 is a real object; background is -1.
## Tests
- test_units.py: 11 synthetic tests pass.
- test_relift_t.py on the real dump, assertions only:
  - t = GT gives t == e on all 117 items;
  - served masks give t == a and s == a;
  - s = GT gives s == e;
  - a, e and the stats equal a fresh relift run.
- test_launch_dry.sh passes.
## CPU rehearsal (nothing scored)
- arkitscenes/41126645, arm t, 32 anchors: 418 s, finite scores, 7.4 GiB.
- scannet/scene0166_00, arm s, 4 anchors: 103 s, finite.
SHA256SUMS_GTC covers 58 files.
