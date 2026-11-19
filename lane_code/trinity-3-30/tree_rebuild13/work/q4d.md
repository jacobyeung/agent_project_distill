# Read-only investigation (once) for lane tree_rebuild: can N's config hold the tower arm's pose-scale parameters fixed, without a tree change?

You investigate; you do not change anything. You run once, read-only, on trinity-1-18; nobody answers questions. Your final message is the answer, at most 25 lines, every claim with file:line.

## Context
Vehicle P (run 6ed2c7aa) trained from step 544 to 400. Its tower arm's returned camera displacement grew (median ratio 1.014 against step 544), because the scale that multiplies the tower's pose moved with the checkpoint. Answers copy the returned value. The orchestrator asks whether vehicle N's trainer tree has a CONFIGURATION field, with no tree change, that holds the parameters producing that scale fixed during N's training. Candidates: a freeze list, trainable groups, a geometry `finetune.lr_scale` of 0 (see `student_pilot/carrier_c1_sweep.py:131`), a pose-scale rule (`student_pilot/tower_scale_rule.py`), adapter target lists, or a scale target switch.

The tree is `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w23/work/tree_r1` (seal 5b349b18). N's step-400 configs are in `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w23/work/build21/inputs/config.json`, the kit's decoded `work/build21/kits/q/k/n.json`, and P's runtime config `/scratch/jjyeung/orch_n30/tree_rebuild10_w/inputs/p_runtime/`.

## Answer
1. Which module and tensors produce the scale the tower arm applies to the pose at serving time, and which training code path (the production trainer that N's launch runs, through launch_r1/entry.py) builds the optimizer for them.
2. Is there a config field that excludes them from the optimizer, or sets their learning rate and weight decay to exactly zero, so that they stay bit-identical after optimizer steps? Name the field's path in N's config, its current value in N's config, and how to set it. Say whether AdamW weight decay or any EMA, re-init or loading path would still move them.
3. If no such field exists, name the smallest tree change.

## Rules
Read-only. No ssh, network, GPU, Git, tmux, scheduler or another agent. Never list, search or grep on /home or /data*. Any process runs under nice -n 10, at most 8 threads, under 20 GB RAM.
