# Integrated E2E trainer build

Status: CPU CODE COMPLETE; INPUT/GPU GATES PENDING. The tree is `/scratch/jjyeung/orch_cd/stageb_merge/work/c1mix_e2e`.

## Question

Can one trainer preserve both parents, integrate tower and mask-ground decode, and carry object-routing and camera-routing recipes without a prompt-mode flag?

## Built

- The trainer combines 8619839, Stage B 75f5bd7, d0523b1 boundary exports, tower v2 and backend v2. All three plain-diff patches reproduce the same tree at zero fuzz.
- E2E-1G routes camera motion and the winning object families. E2E-1C routes camera motion and keeps objects direct. Both train MDG and keep easy-direction, room and camera-object questions direct.
- Both use world 4/reference 32, 32 frames, one pose stream (A2 a2v3 + A3 a3v2), full LM training and a global batch of 160. Each rank receives pose 8, VQA 16, pointing 4, MDG 4 and routing 8. Matching stream order preserves sampler RNG assignments; fixed-row losses and plans match exactly.
- Atomic ground/gap tokens share one FP32 input/output row owner across main and query forwards. Exports and warm starts preserve those rows. LoRA opens only in the isolated MDG query. Routing cross-entropy teaches main-stream emission; MDG-only training does not.
- Milestones and the leg boundary export the LM with heads. Complete rows cap at 10k; routing suffixes cap at 5k, without truncation. A4 r_s and flagged CP2 r2 are refused.
- Unknown literal names remain eligible. Vocabulary membership and disconnected mask components are audit-only. Instance selection belongs to the object-first selector.

## Evidence

The final broad suite passes 439/459 tests with 20 explicit skips and no failures/errors. Every inherited scoped test method is present. Both variants pass 160/160 native CPU fixture rows across all five streams. Their exact row plans, tokens, losses and components match.

Four longest native-tokenized v3.12.2 examples pass; the largest contains 1847 tokens (suffix 759). Fixture MDG prefixes/calls contain 227/241 tokens. No forwarded first-batch fixture exceeds 10k. Production RGB and 9B training batches remain PENDING-INPUT.

All nine required review mutations are detected on a private copy, with an unmodified passing control. Five independent GT objects pass geometry within 0.00941986 m and C2 replay 5/5. Cached tower parity passes ten scenes; r1 replay passes 2000/2000 responses. Live extraction verifies 64 RGB hashes but lacks governed weights.

The approved integrated real T0 + MDG-A repeat passes: every output array matches, C2 replays 13 calls byte for byte, 5 seen calls register points, and 6 gaps are seen (1 between distinct objects). It uses the same s_0718/best/step_00002100 artifact and six labels as sibling v2.

The merged run takes 3744.4 seconds and peaks at 40.27 GiB RSS. The sibling reports 2477.8 seconds and legacy RSS 42.21 (Linux KiB/1e6); the corresponding merged field is 42.22, a difference of +0.01, with runtime difference +1266.6 seconds. Workload and node contention limit throughput comparisons. The run uses nice 10, at most eight Torch threads, with minimum usable RAM 290.3 GB. Prompt/query-max/complete-decode tokens are 4713/4721/5564; over-10k flag: False. It uses own geometry; live tower extraction remains pending.

The calls are scripted. This establishes backend execution and native-query parity. Learned routing, benchmark accuracy and GPU fit require separate tests. Component counts govern only audit metadata; the updated admission rule does not establish model-output quality.
