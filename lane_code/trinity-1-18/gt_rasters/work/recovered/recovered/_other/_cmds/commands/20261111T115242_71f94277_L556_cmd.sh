<!-- recovered by seal_plan: transcript=71f94277 line=556 utc=2026-11-11T11:52:42.629Z kind=commands original_path=(bash command)  -->
m=/home/jjyeung/.claude/projects/-scratch-jjyeung-orch-home-distill/memory; cat > $m/lane-intent-two-goals-20261111.md <<'EOF'
---
name: lane-intent-two-goals-20261111
description: The user's statement of the distillation lane's two intents (2026-11-11) - a SOTA 9B spatial VLM that beats the frontier closed models, then VLA fine-tuning that is cheaper and better from that model
metadata:
  type: project
---

The user, 2026-11-11 ~03:55 PT ("remember, the intent is"):

1. **Train a new SOTA spatial-understanding VLM.** "i strongly believe we can beat astra, argon, carbon with our 9B model! with GT perception we get 80+% on the benchmarks right?" The user's open design questions: how to improve the current model, how much data it needs, whether to add a different vision encoder, whether to change attention for better pose and depth, whether to add G3T or a 4D reconstruction model as a vision encoder, and how to combine those features with the VLM.
2. **VLA payoff.** "given a strong spatial understanding model, we hypothesize it is much easier to finetune on vla tasks, eg fewer samples, so more efficient finetuning, also we can get better performance on vla tasks." Both sample efficiency and final performance count.

The user also asked (same hour) that all model, action-head (including a diffusion head) and VLA-test code be developed and tested ahead of time, "so when it's time to actually run, we don't need to debug and waste time".

**Why:** intent 1 is the paper's main result and intent 2 its payoff; the GT-perception ceiling (80.1 on 655 dev items, [[toolprog-results-20261107]]) is the user's evidence that perception, not reasoning, is the limit.

**How to apply:** rank every experiment by how much it closes the gap to the GT-perception ceiling or to the frontier bars; keep VLA code (heads, loaders, evaluators) built and CPU-tested before the model is ready ([[build-experiments-first]]). Design records: distill_design/MODEL_IMPROVEMENT_PLAN_20261111.md and VLA_ACTION_HEAD_DESIGN_20261111.md. Related: [[goal-nov1-traces-beat-direct]], [[paper-pitch-downstream-vla-efficiency]], [[downstream-priority-direction-navigation]], [[drastic-architecture-ok-20261109]].
EOF
echo '- **READ FIRST, USER 11-11:** [Lane intent: two goals](lane-intent-two-goals-20261111.md) SOTA 9B spatial VLM beating frontier closed models; then cheaper + better VLA fine-tuning; build all code ahead' >> $m/MEMORY.md
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) orch-home-distill-79: USER ~11:50-11:58Z restated the lane's two intents (memory lane-intent-two-goals-20261111) and asked for all model / action-head / VLA-test code to be built and tested ahead. Dispatched three Claude subagents (background): vla_inv (Sonnet medium; inventory -> /scratch/jjyeung/orch_cd/vla_inv/INVENTORY.md), vla_design (Opus max; record distill_design/VLA_ACTION_HEAD_DESIGN_20261111.md), model_design (Opus max; record distill_design/MODEL_IMPROVEMENT_PLAN_20261111.md). Next: on the inventory, launch build lanes (action heads x3 behind one interface + CPU tests; LIBERO and R2R-CE loaders and evaluators); on each design, cross-family refute, then builds from its build list." >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md; date -u +%H:%MZ