# GTC-B kit: arm b (t_big), the GT instance seeded on its largest anchor (lever6; ORCH ANSWER 2026-11-21T21:37Z)
## Changes (copy of lever6/gtc/kit; lever6/gtc is read-only)
- gtc_common.py: OUT = gtcb/out; GTC_OUT = lever6/gtc/out (FRAMES_GTC.json, SEEDS_GTC.json, the t and s tracks).
- seeds.py: the b seed is the GT instance on the anchor with the largest 240x320 area (argmax, ties to the lowest); one unit per (capture, instance), carried both ways. It rebuilds t and s and asserts the rebuilt SEEDS_GTC.json is byte-identical and each npz bit-identical; it writes only b (out/SEEDS_GTCB.json, out/seeds/*.npz). Only the wording of the t-rule string changed, to match the file.
- track.py: arm b only, forward then backward, K1 carry rule.
- launch_gpu.sh: arm b only. It refuses the head node and trinity-1-13, 0-23, 0-8, 3-23 and 0-18. A card counts as empty at <= 100 MiB used in both readings, 300 s apart. It checks SHA256SUMS_GTCB and runs at normal priority on 0-13, under vnice elsewhere.
- relift_t.py: t and s from gtc/out/track, b from gtcb/out/track.
  - All t and s outputs must equal RELIFT_GTC.json (checked without printing).
  - Section b holds b, b-a, b-t (descriptive), e-a and the share, with the room bootstrap, overall and per dataset; b's precision and recall against GT; the seed facts; and the reading (the t bars on b-a, no guard).
  - Output: out/RELIFT_GTCB.json.
## Seed facts (not results)
- 169 units; 233 of 234 operands are seeded, and 1 has no visible anchor.
- Median seed area: 4,827 px (ARKit 12,915; ScanNet/ScanNet++ 3,336.5).
- 11 seeds are under 200 px (ARKit 1, ScanNet 10) and 6 under 50 px; the smallest is 1 px.
- 98 of 117 items have every b seed at 200 px or more.
## GPU forecast
About 201-218 s; peak memory at most 4.8 GiB reserved.
## Launch on trinity-0-13 (identical paths)
- Copy 0.6 MB: gtcb/kit (with tests), gtcb/out/SEEDS_GTCB.json, gtcb/out/seeds/*.npz and gtcb/SHA256SUMS_GTCB. 0-13 already holds the GTC inputs.
- Start: `cd /scratch/jjyeung/orch_n30/lever6/gtcb && tmux new-session -d -s gtcb_gpu 'bash kit/launch_gpu.sh b'`.
- Bring gtcb/out/track back to 2-28. Then: `cd kit && CUDA_VISIBLE_DEVICES='' nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B relift_t.py`.
## Tests (all pass)
- test_units.py: 19/19.
- test_relift_t.py on the real dump: 699 s, assertions only. b = GT gives e; real t and s equal RELIFT_GTC; b = served gives a; b = t gives t; an incomplete b directory is refused.
- test_launch_dry.sh passes.
- CPU rehearsal of b on 4 anchors: 56 s, finite, not scored.
- SHA256SUMS_GTCB covers 58 files; this report is not among them.
