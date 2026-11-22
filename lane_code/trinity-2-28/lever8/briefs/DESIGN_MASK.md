# Draft a design paper: whole-object mask sources for the routed reader after SAM 3's tracker (nothing built, nothing run)
You are a research analyst for lane lever8. Goal of the project: a ~9B spatial VLM whose chain of thought calls heads inside its own checkpoint (ReVSI first), end to end from RGB. The routed reader answers routed-distance items by grounding named objects into masks, lifting them with served depth and cameras, and measuring.
Question: which whole-object mask source should be priced next, now that SAM 3's tracker has been priced? Rank the candidates. The orchestrator and the user rule on it.

## What is settled (cite, do not redo)
On 117 dev routed-distance items (step 544, paired inside dump 174135): perfect masks +13.8 [+5.5, +22.3]; choosing among the reader's own candidates -0.2; the voted box flat. SAM 3's tracker seeded with the true mask: first visible frame +2.7; largest anchor over 32 served frames +4.0 [-5.6, +14.4] (ARKit -9.1); dense frames +7.9 [-1.7, +17.4] pooled (ARKit repaired, dense minus sparse +10.3 [+0.0, +30.9]; ScanNet+ScanNet++ +10.5 [-1.4, +21.5]); reader's own mask as seed -4.8. About half of the perfect-mask gain is recovered at best; a tracker, if built, runs over the dense video.

## Read (bounded reads only; grep inside one named file is fine)
- Plan of record /data2/jjyeung/agent_project_data/distill_design/ROUTED_READER_LEVER_PLAN_20261120.md: lines 1-60, 109-162, 201-290 (rank 1 and the GTC/GTC-B/GTC-D sections).
- /data2/jjyeung/agent_project_data/distill_design/MASK_CARRY_K1_TRAIN_20261119.md (the K1 carry of 2026-11-19).
- /data2/jjyeung/agent_project_data/distill_design/GROUNDING_CEILING_T2_20261120.md (the 2D-point read of 2026-11-20).
- /data2/jjyeung/agent_project_data/distill_design/MASK_QUALITY_DESIGN_20261119.md (earlier mask-quality design; candidates and costs).
- /data2/jjyeung/agent_project_data/distill_design/GROUNDING_FUNNEL_20261120.md and GROUNDING_LABEL_CONSUMER_SPEC_20261120.md (OWNHEAD, COVER64, the dev-S1 visibility census); NV_KEY_SPEND_PLAN_20261120.md for what the census and labels certified.
- INDEX.md in that folder (grep it for 'mask', 'SAM', 'census', 'pointing', 'box') to find any other record you need; open only named files.
- Arm results files: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/lever/files/gtc/ and files/gtcd/ (list each single directory; read the small .md/.json results, per-frame precision and recall per dataset).

## Candidates (each one, plus any other the plan or these records name)
1. SAM 3's detector with a text prompt per frame (open-vocabulary, the object name as prompt).
2. A SAM 3 detector fine-tune (on which labels, which rooms; exclusions: K1 held-out, dev-S1, R0-dev and benchmark scenes never train).
3. The reader's own box or mask head inside the checkpoint (OWNHEAD; the model's own pointing ceilings 15/81 and 22/81 from B6).
4. The tracker over dense video with a deployable seed (which seed: detector, own head, served best mask; the served-seed arm lost -4.8).
5. Others the records name (e.g. multi-seed or re-seeded tracking, voting across frames, amodal extent).

For each, write: what it would supply that the served masks do not (whole object vs fragment, right instance vs wrong, coverage of frames); what we already hold that prices part of it (K1 carry, the 2D-point read, the visibility census, tonight's arms; quote numbers with intervals and the file); the cheapest decisive test on the 117 dev items with registered bars in the plan's convention (e.g. arm minus a >= 8 with lower bound > 0 is a source; <= 4 with upper bound < 8 closes it; else undecided) and its cost (GPU-hours, card, bytes moved); its cost at serving time (per item, frames, extra model passes); and whether it keeps the model end to end from RGB with heads inside its own checkpoint. Then rank them with reasons, name what each outcome would make us build, and list options rejected with reasons, what might not work and how we would notice.

## Output
Write /scratch/jjyeung/orch_n30/lever8/design/MASK_SOURCE_DESIGN.md (at most about 180 lines, plain words, numbers with their files). Do not edit the plan record or INDEX.md; lever8 does that. Final message: 5 lines at most naming the file and the top-ranked candidate.
## Rules for this subagent (copy of the lane's rules of the road; obey all)
- Read /home/jjyeung/.claude/CLAUDE.md section "Key Trinity Cluster Rules" and /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md first; they win over this brief.
- Every stream over 20 MB that crosses the head node or touches /home or /data* registers with the IO governor first. You need none: read only the named files, in bounded parts (sed -n, head, tail); no recursive grep/find/du/ls -R on /home or /data*; grep inside one named file is fine.
- No Git command. No ssh, no Orchard call, no GPU use, no job submission, no Gemini/OpenRouter/NV call. Nothing is run or built except what this brief names.
- Trinity cards (for reference only; you launch nothing): trinity-0-13 at normal priority, another shared node only under vnice, never trinity-1-13, 0-23, 0-8, 3-23 or 0-18.
- A local rehearsal of any kit runs the job's own launcher line, and a child that dies must leave its cause.
- Work from /scratch; write your report to the file this brief names; your final message is 5 lines at most and names the file.
- Write no files outside /scratch/jjyeung/orch_n30/lever8/. Delete nothing.
- Prose: complete sentences, characters as subjects, actions as verbs; no metadiscourse.
