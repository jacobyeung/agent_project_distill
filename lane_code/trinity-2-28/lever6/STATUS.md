# lever6 STATUS (trinity-2-28; started 19:53Z 11-21; successor of lever5). Successor resumes from this file alone.
Lane dir /scratch/jjyeung/orch_n30/lever6. Ledger lever6/work/ORCHARD_LEDGER.jsonl. Orchard: tools/ossh.sh; general one job of ours at most; never advanced. Nothing of ours runs on Orchard or Trinity GPUs now; no stream open.
## All five owed items are done (RESULTs in events/lever; plan record ROUTED_READER_LEVER_PLAN_20261120.md carries each)
1. K5 (token adba6b82bdb9d; kit lever6/k5b/kit; returns lever6/k5b/ret/{cpu,g0,g1}; score lever6/k5b/ret/scored). The tower alone is order-independent under the default settings. The deterministic settings are bit-stable but move the outputs (median 9 mm, p90 0.19 m, max 1.23 m / 79 deg) and cost x1.15. They are not proposed for serving. RESULT 2301Z. The first kit (a51f1ee88f0c9) died in its CPU check on missing bwrap bind dirs; it was fixed and reviewed (RESULTs 2015Z, 2116Z).
2. Noise floor, option B: 0 on all camera types (450/450 reproduced). It is vacuous because the history comes from the LM sharing the process. QUESTION in RESULT 2301Z (default: no new build; option A or a tower-after-LM arm prices it). Files lever6/nf.
3. GTC (RULING 1939Z A): undecided, t-a +2.7 [-9.5,+13.6]; s-a -4.8 (RESULT 2131Z). GTC-B t_big (ANSWER 2137Z): undecided, b-a +4.0 [-5.6,+14.4]; ScanNet/ScanNet++ +9.2, ARKit -9.1; the seed does not bind, and the carry loses on ARKit (RESULT 2241Z). Kits lever6/gtc, lever6/gtcb; inputs and tracks also on trinity-0-13 at the same paths.
4. R0 pair 2: different rooms; R0-dev keeps 98 rooms (RESULT 1959Z).
5. Plan record current (sections GTC, GTC result, GTC-B, GTC-B result, K5/noise floor).
## Owed now: arm d (ORCH ANSWER 2245Z), the b seed carried over dense frames
- DONE: inventory (lever6/gtcd/INVENTORY_D.md) and registration in the plan record (section 'Rank 1 follow-up (GTC-D)', plan line ~259).
- Dense sources:
  - ARKit: /data3/shared/datasets/arkitscenes/3dod/Training/<id>/<id>_frames/lowres_wide at stride 2, 0.9 GB.
  - ScanNet: /data3/shared/datasets/scannet/scans/<scene>/<scene>.sens at stride 6, 10.9 GB.
  - ScanNet++: /data2/jjyeung/raw_datasets/scannetpp/data/<id>/iphone/rgb.mkv at stride 24, 8.7 GB.
  - About 100 GPU-min.
- NEXT, in order:
  1. Build (Claude opus high, at most two builders). Copy lever6/gtcb to lever6/gtcd/kit.
     - Dense loader: decode .sens, mkv and lowres with the served path's own decoding and resize, and assert that each anchor frame reproduces its served PNG sha256 (FRAMES_GTC.json); report any mismatch per capture.
     - Track arm d both ways over the dense sequence, with embeddings once per frame; read out at the 32 anchors.
     - relift_t gains d, d-b, d-a, the share and P/R; the verdict uses the same bars plus "d no better than b".
     - Tests as for b.
     - The stage scripts write to /scratch only: lever6/gtcd/dense/<dataset>/...; a .sens or mkv may be decoded on the fly or kept on /scratch.
  2. The three governed streams, registered at once: one record each, started stopped, register.py --tier 3 --allow-resume, ratelimit.py in the path, pattern lever6/r0p2/stage.sh, an orchestrator priority if given, else 950.
     - Per the IO governor README, use launch_paced_archive.py only for archives. These are file lists, so use tar -T list | ratelimit | tar x.
     - Watch STATE.md; rename each record .done when finished.
  3. Fresh review (opus high, files and criteria only).
  4. Copy dense frames and kit to trinity-0-13 over IB (same paths); a fresh nvidia-smi reading; launch in tmux there (normal priority; never 1-13, 0-23, 0-8, 3-23, 0-18).
  5. Copy the tracks back; relift; RESULT with d-a, d-b, share, P/R, per dataset; plan record result.
## Open
- QUESTION 2301Z (noise floor next step), default no build. K1-train S_GT resume waits for the user (U7), not ours.
## Mirrors (trinity-0-13:/scratch/jjyeung/n30_mirror/lever6/)
- mirror_lever6.tar: sha 3d397e16...965a (nf, k5b, gtc kits and RELIFT_GTC.json).
- mirror_lever6b.tar: sha c6364293a60f6b6bfd3bc427f175d4360c760d86a96941f254bd2ffa8482e356 (K5 returns, NF out, the GTC-B kit and result).
- Orchard: /project/community/jjyeung/adba6b82bdb9d (K5 package and returns).
## Removal candidates: lever6/REMOVAL_CANDIDATES.md; lever6/nf/REMOVAL_CANDIDATES_NF.txt; Orchard /project/community/jjyeung/a51f1ee88f0c9; trinity-0-13 /scratch/jjyeung/orch_n30/lever6 (staged GTC inputs, about 3.7 GB) once no longer needed.
