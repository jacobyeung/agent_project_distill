# Open questions (sb_mask_carry), each with the default the kit acts on

PROMPT.md limits writes to this workspace, so these rows are not in `/data2/jjyeung/agent_project_data/SAVED_USER_QUESTIONS.md`; copy them there if wanted.

| # | Question | Default (in force) |
|---|---|---|
| 1 | The spec's order puts S_PHR last, so a projection drop removes it first, yet the bars read on S_PHR now that PHRASE_SET.json is frozen. Should S_PHR move ahead of S_GT/A32? | Keep the spec order. S_PHR differs from S_A0 on 20 of 770 objects (heater); the other 744 seeded objects reuse the S_A0 track, so S_PHR costs about 1% of the pass. If both S_PHR sets drop, the bars read on S_A0 and CARRY_DECISION.json says so. |
| 2 | "vnice.sh off trinity-0-13": run anywhere except trinity-0-13 under vnice, or something else? | The launcher refuses trinity-0-13 and the head node, and always wraps the job in vnice.sh. |
| 3 | The spec estimates 1.4 GPU-h; the derived estimate on an RTX A6000 reaches the 2.0 h stop (KIT_REPORT.md). Raise the cap? | No. The cap stays 2.0 h; the 10-capture projection drops trailing sets in order. |
