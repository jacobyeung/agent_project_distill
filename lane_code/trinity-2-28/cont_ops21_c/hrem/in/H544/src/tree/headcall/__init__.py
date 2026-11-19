"""Phase 2 on the full fine-tuning trainer: the student calls its own depth and pose heads mid-trace
(design and deviations: DESIGN_HEADCALL_FULLFT.md at the tree root).

Ported from phase2-headcall-opus @ 83c2d47 (agent_project_distill, headcall/); the converters, the first-hit packs and
the held-out probe builder stay there, and their outputs enter this tree only as pinned sidecars and rows.

Modules:
  protocol  call and response text, robust call parsing and validation
  geometry  GT pose and pixel conventions, the rotation angles and the unprojection the student applies
  derive    derived text (points, distances, closest candidate, directions, ego-motion) computed only from calls and
            printed responses, and the one decision rule converters, scheduled sampling and the gate share
  heads     head backends: oracle, noisy, shuffled (real outputs permuted across samples), the trainer's HeadSession
  phase1    the trainer's head code in this tree: head API, carriers, the camera-hooked prefill, gate thresholds
  training  tool-response masking, scheduled sampling, head-query targets
  rows      the headcall training block: sidecar join, tool-response masking, forced carriers, queried depth targets
            and scheduled sampling inside ddp_training.train (replaces phase 2's runtime patch, trainer_wiring)
  decode    HF decode loop with call interception (and a vLLM segment decoder)
  eval_hook head-call generation for the evaluator plus the head-vs-shuffled ablation
  gate_eval the heads' accuracy gate on the held-out probe rows (full fine-tuning checkpoints included)
"""
