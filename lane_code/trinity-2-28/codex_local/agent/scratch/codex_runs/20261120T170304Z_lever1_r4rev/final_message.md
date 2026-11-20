LEGAL WITH CONDITIONS

Conditions:
- Source each template from public task-description text; record its exact source and wording. Do not extract templates from benchmark item files, examples containing item-specific information, videos, answers, or results.
- Freeze the template set, call detector, 64-token budget, and 95% gate before the diagnostic. Do not select or revise them using ReVSI scores or correctness.
- Use eligible development rooms for the diagnostic and eligible training rooms for arm D. Exclude benchmark rooms and their physical-room siblings; exclude every R0 room from training.
- Use R0-dev only to measure call placement and trigger the predefined training intervention. Do not optimize inference prompts, rewrite candidate templates adaptively, or fit thresholds against R0-dev.
- Treat room separation as conditional on the recorded exclusion coverage, which has unresolved gaps.

Evidence and answers:

1. **Section 7 permits both uses under these conditions.** Its controlling test is inference-time availability, and it permits question/category-specific logic with disclosure. A public, generic task description available to any system is not inherently hidden benchmark information. Applying that wording to independent development or training examples is therefore permissible. This is an interpretation of the rule, not an express template-specific exemption. Public hosting alone does not authorize benchmark answers, oracle information, or correctness-derived state.  
   Evidence: `/home/jjyeung/agent_project/AGENTS.md:546–562`.

2. **Wording overlap and scene overlap are distinct.** The exclusion record groups scenes by physical room, rescans, and venues; it does not establish a wording prohibition. The v7 precedent supports conditional admission of borrowed wording but does not settle legality: it records 8,511 rewritten rows, explicitly leaves the legality review outstanding, and requires disclosure.  
   Evidence: `BENCH_SCENE_EXCLUSIONS_20261108.md:11–15`; `ROWS_V7_R1_20261117.md:9,11,33,39`.

3. **Section 7.0a creates no answer-bank obligation for this unscored call-placement diagnostic.** Its archival requirement applies to every scored cell’s per-question answer files. If a later arm-D evaluation produces scored answers—including the plan’s template-MRA check—the requirement applies then. Existing banks remain protected.  
   Evidence: `/home/jjyeung/agent_project/AGENTS.md:569–579`; `ROUTED_READER_LEVER_PLAN_20261120.md:115`.

4. **The R0-dev restriction does not forbid this fixed diagnostic or a predefined training-row intervention.** Measuring call placement does not itself fit a prompt or threshold. Selecting a failing, already-fixed template family for training on separate rooms is development-guided training design; it must not become optimization of deployed prompts against R0-dev. Training-room separation alone would not excuse such prompt fitting. The 95% gate must remain fixed.  
   Evidence: `R0_RESERVE_SCENES_20261116.md:5`; `ROUTED_READER_LEVER_PLAN_20261120.md:67–71,115`.

5. **Later paper numbers must disclose the borrowed templates and any resulting training intervention.** State the public source, affected training families/counts, R0-dev selection role, and applicable evaluation limitations. Do not describe R0-dev as untouched after it guides arm D, or claim template-independent evaluation. Archive later scored cells under §7.0a.  
   Evidence: `/home/jjyeung/agent_project/AGENTS.md:556–558,569–579`; `ROWS_V7_R1_20261117.md:39`.

All abbreviated evidence filenames are under `/data2/jjyeung/agent_project_data/distill_design/`. The current WORD section is at lines 67–72, not 104–109. R0 registers 100 development rooms, with 98 usable rooms; its exclusion review remains **UNPROVEN**, with no collision found and documented coverage gaps (`R0_RESERVE_SCENES_20261116.md:9,17,21`).

`REVIEW_R4.md` was not written because this session’s filesystem policy permits reads only.