# lever6 STATUS (trinity-2-28; started 19:53Z 11-21; successor of lever5). Successor resumes from this file alone.
Lane dir /scratch/jjyeung/orch_n30/lever6. Ledger lever6/work/ORCHARD_LEDGER.jsonl. Orchard: tools/ossh.sh; general one job of ours at most; never advanced. Nothing of ours runs on Orchard or Trinity GPUs now; no stream open.
## All five owed items are done (RESULTs in events/lever; plan record ROUTED_READER_LEVER_PLAN_20261120.md carries each)
1. K5 (token adba6b82bdb9d; kit lever6/k5b/kit; returns lever6/k5b/ret/{cpu,g0,g1}; score lever6/k5b/ret/scored). The tower alone is order-independent under the default settings. The deterministic settings are bit-stable but move the outputs (median 9 mm, p90 0.19 m, max 1.23 m / 79 deg) and cost x1.15. They are not proposed for serving. RESULT 2301Z. The first kit (a51f1ee88f0c9) died in its CPU check on missing bwrap bind dirs; it was fixed and reviewed (RESULTs 2015Z, 2116Z).
2. Noise floor, option B: 0 on all camera types (450/450 reproduced). It is vacuous because the history comes from the LM sharing the process. QUESTION in RESULT 2301Z (default: no new build; option A or a tower-after-LM arm prices it). Files lever6/nf.
3. GTC (RULING 1939Z A): undecided, t-a +2.7 [-9.5,+13.6]; s-a -4.8 (RESULT 2131Z). GTC-B t_big (ANSWER 2137Z): undecided, b-a +4.0 [-5.6,+14.4]; ScanNet/ScanNet++ +9.2, ARKit -9.1; the seed does not bind, and the carry loses on ARKit (RESULT 2241Z). Kits lever6/gtc, lever6/gtcb; inputs and tracks also on trinity-0-13 at the same paths.
4. R0 pair 2: different rooms; R0-dev keeps 98 rooms (RESULT 1959Z).
5. Plan record current (sections GTC, GTC result, GTC-B, GTC-B result, K5/noise floor).
## Owed now: arm d (ORCH ANSWER 2245Z), the b seed carried over dense frames
- Plan:
  1. Inventory (Sonnet medium; brief lever6/gtcd/BRIEF_INV.md -> lever6/gtcd/INVENTORY_D.md): where the dense frames of the 46 captures are, stride per dataset, governed bytes from /data*, GPU time on 0-13. Running now.
  2. Register arm d in the plan record (a new 'GTC-D' section after the GTC-B result). Same seed as b; the tracker runs both ways over the dense sequence and its masks are read at the 32 anchors. Same bars. Add d-b paired (the price of dense carrying).
     - Readings: d clears the first bar -> build a tracker over the dense video, once per clip, seeded on a well-visible frame. d no better than b -> the plan names the next source.
     - If a dataset needs more than 30 GB or more than 2 GPU-h, register the cheap datasets first.
  3. Build (opus high): copy lever6/gtcb -> lever6/gtcd, add a dense frame loader and a read-out at the anchors.
  4. Fresh review (opus high).
  5. Fresh nvidia-smi reading; run on a trinity-0-13 card (normal priority).
  6. relift; RESULT; plan record.
## Open
- QUESTION 2301Z (noise floor next step), default no build. K1-train S_GT resume waits for the user (U7), not ours.
## Mirrors (trinity-0-13:/scratch/jjyeung/n30_mirror/lever6/)
- mirror_lever6.tar: sha 3d397e16...965a (nf, k5b, gtc kits and RELIFT_GTC.json).
- mirror_lever6b.tar: sha c6364293a60f6b6bfd3bc427f175d4360c760d86a96941f254bd2ffa8482e356 (K5 returns, NF out, the GTC-B kit and result).
- Orchard: /project/community/jjyeung/adba6b82bdb9d (K5 package and returns).
## Removal candidates: lever6/REMOVAL_CANDIDATES.md; lever6/nf/REMOVAL_CANDIDATES_NF.txt; Orchard /project/community/jjyeung/a51f1ee88f0c9; trinity-0-13 /scratch/jjyeung/orch_n30/lever6 (staged GTC inputs, about 3.7 GB) once no longer needed.
