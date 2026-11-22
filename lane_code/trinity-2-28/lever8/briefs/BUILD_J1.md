# Build J1: SAM 3's frozen detector per frame (h1) and two oracle ceilings (h0, k), relifted inside dump 174135 on the 117 dev items (lane lever8, trinity-2-28; ORCH RULING 2026-11-22T04:38Z)
You are the build subagent of lane lever8. Check `hostname -s` prints trinity-2-28; stop if it prints `trinity`. Codex is logged out; you build.

## Binding for you
- NO GPU (CUDA_VISIBLE_DEVICES='' everywhere), NO ssh, NO stream, NO Orchard, NO Git, no deletion. CPU work under nice -n 10, threads <= 8. Write only under /scratch/jjyeung/orch_n30/lever8/j1. Every other folder (lever5/r1x, lever6, lever7, lever1_c, grd_funnel1, cont_ops24_c, sb_cachk, b01ec87a6f29b) is a read-only input; import code from them unchanged, never edit it.
- If an input you need is not on this node's /scratch, STOP and write j1/FILES_NEEDED.md (exact paths, host, bytes); lever8 moves it.
- Do not compute or print any cell value or score of h1, h0 or k on real outputs, and do not run the scorer on real detector output. The reading is fixed below; a fresh review checks the kit before the GPU run. Synthetic tests only; the real CPU rehearsal may print timing and finite-mask counts, nothing scored.

## Design (read first): /scratch/jjyeung/orch_n30/lever8/design/MASK_SOURCE_DESIGN.md, section "1. Frozen SAM 3 detector" and "Registered bars".

## Inputs
- Relift code (reviewed): /scratch/jjyeung/orch_n30/lever5/r1x/r1/relift.py (cells a..g; cells c and d read the dump's proposal pool). Dump /scratch/jjyeung/orch_n30/lever1_c/r1/returned/0.gz with RETURN_RECEIPT.json (pass --depth and --receipt as earlier kits do). Item manifest /scratch/jjyeung/orch_n30/grd_funnel1/kit/rerun2/items544.json. Population: relift's 117 eligible items on 46 captures.
- Pattern kits to extend (copy into j1/kit, then change): /scratch/jjyeung/orch_n30/lever7/gtcd/kit (relift_t.py, gtc_common.py, launch_gpu.sh, run_cpu_rehearsal.sh, seal.sh, tests/; REPORT_GTCD.md describes it) and /scratch/jjyeung/orch_n30/lever6/gtc/kit (frames.py: the 32 served anchors per capture checked against frame_binding_sha256; seeds.py: the bound GT instance `target`). Anchor frames: lever6/gtc/out/FRAMES_GTC.json for ScanNet and ScanNet++; ARKit anchors from /scratch/jjyeung/orch_n30/lever7/gtcd/arkit/frames_k6 (re-decoded with OpenCV 4.14.0, 576/576 anchors byte-equal; REPORT_CV2.md). Every anchor's sha256 checked against the binding; a mismatch fails the capture, never substitutes.
- The served SAM 3 detector path: the read package b9ef552934627 that produced dump 174135's pool (find its grounding call code under /scratch/jjyeung/b01ec87a6f29b and /scratch/jjyeung/orch_n30/lever1_c/r1; the 2D-point read's kit /scratch/jjyeung/orch_n30/cont_ops24_c is another served-path driver). Weights /scratch/jjyeung/b01ec87a6f29b/d/k/sam3.pt; source /scratch/jjyeung/b01ec87a6f29b/d/s/sam3; envs /scratch/jjyeung/envs/sam3_capretry_native_v1, sam3_scipy_ovl, p1cpu. Use the served contract exactly (prompt = the name the model writes in its ground call, its alias rule, score/presence floor, proposal cap, mask resize to the 240x320 grid); find each value in code and cite file:line in the report.

## Arms (masks on the 32 served anchors, relift's (32,240,320) grid)
- h1 (deployable): one SAM 3 image pass per anchor per operand name, served contract; on each anchor keep the top proposal by the served ranking score (score x presence if that is the served rule) above the served floor; empty otherwise. No linker, no track selection.
- h0 (pool oracle): same pass; on each anchor the retained proposal with highest IoU against the bound GT instance, kept if IoU >= 0.5; empty where GT is empty or no proposal reaches 0.5.
- k (box oracle): the bound GT instance's tight box as SAM 3's box prompt on every anchor where GT is non-empty, no text; the best mask by SAM 3's score; empty where GT is empty.
- Parity stop: J1's text pass must reproduce dump 174135's proposal pool (the masks cells c/d read) on >= 95% of operand-frames by a stated match rule (IoU >= 0.95 and same count, or say what matches). Below 95% the relift refuses to read h1 and h0 and says so; k is still read.

## Reading (fixed now; code it, print nothing real)
- Paired on the same 117 items with relift's room bootstrap (10,000 draws, same seed rule): for X in h1, h0, k: X - a with interval; share (X - a)/(e - a); verdict: X - a >= 8 and lower bound > 0 -> "source" (for h0 and k read "opens"); X - a <= 4 and upper bound < 8 -> "closes"; else "undecided". All 117 items decide.
- Per dataset (ARKit, ScanNet, ScanNet++ separately) with item and room counts beside every number; per-dataset values do not decide.
- Per-frame mask precision and recall at the anchors against the GT instance for a, h1, h0, k per dataset (define over frames where GT or prediction is non-empty; say it), and the count of anchors where the arm has a mask and GT is empty.
- For each undecided arm: how many paired items (and rooms, at the observed items per room) the interval would need, at the observed per-room spread and mean, to clear the nearer bar; and which rooms could supply them (dev-S1 items outside the 117 and why they were excluded; R0-dev stays unspent; say so).
- a and e must equal relift.py's own cells on the same inputs (assert in-process without printing).
- Per-item output: j1/out/ITEMS_J1.jsonl, one row per (item, arm in a,e,h1,h0,k) with item id, room, dataset, type, per operand frames with a mask and P/R, the lifted distance, the printed answer, GT, the score.
- Output RELIFT_J1.json + RELIFT_J1.md.

## Build under j1/kit
1. frames (reuse), names/prompts per operand, j1 detector pass (GPU job: loads SAM 3 once; per capture embed each anchor once, then text prompts per operand and box prompts for k; writes all proposals compactly (packed bits + scores) so h1 and h0 are chosen on CPU afterwards; per-capture timing, peak memory, EVENTS.jsonl, partial results on a guard).
2. relift_j1.py importing relift.py unchanged.
3. launch_gpu.sh for trinity-0-13, ONE card, normal priority: refuses the head node, trinity-1-13, 0-23, 0-8, 3-23, 0-18 and paths off /scratch; checks the seal; takes two nvidia-smi readings of the chosen card 300 s apart inside the launching command (card <= 100 MiB used both times) and writes them to EVENTS.jsonl; timeout; each child's exit code and stderr to files. `rehearse-cpu <capture>` uses the same inner line (device and capture list only differ).
4. Tests (synthetic, CPU): top-1 rule, IoU-oracle rule, box from GT, resize, parity matcher, P/R toy, relift_j1 with toy outputs equal to GT (h1 = e) and equal to served masks (h1 = a) on the real dump without printing values, refusal below parity, the needed-items computation on toy data.
5. Real CPU rehearsal via the launcher's own line on the capture with the fewest operand-frames (or its first 4 anchors if over 20 min); a child that dies leaves its cause.
6. A list of what moves to trinity-0-13 (paths, bytes) and back; seal SHA256SUMS_J1; j1/REPORT_J1.md (<= 70 lines): served contract with file:line, arm definitions as built, parity rule, forecast GPU minutes and peak memory, commands for the lane (tar pipe over .ib to 0-13, tmux launch, return, relift), tests and results, rehearsal, removal candidates.
Final message <= 20 lines: forecast, test results, any stop condition, the report path.
## Rules for this subagent (copy of the lane's rules of the road; obey all)
- Read /home/jjyeung/.claude/CLAUDE.md section "Key Trinity Cluster Rules" and /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md first; they win over this brief.
- Every stream over 20 MB that crosses the head node or touches /home or /data* registers with the IO governor first. You need none: read only the named files, in bounded parts (sed -n, head, tail); no recursive grep/find/du/ls -R on /home or /data*; grep inside one named file is fine.
- No Git command. No ssh, no Orchard call, no GPU use, no job submission, no Gemini/OpenRouter/NV call. Nothing is run or built except what this brief names.
- Trinity cards (for reference only; you launch nothing): trinity-0-13 at normal priority, another shared node only under vnice, never trinity-1-13, 0-23, 0-8, 3-23 or 0-18.
- A local rehearsal of any kit runs the job's own launcher line, and a child that dies must leave its cause.
- Work from /scratch; write your report to the file this brief names; your final message is 5 lines at most and names the file.
- Write no files outside /scratch/jjyeung/orch_n30/lever8/. Delete nothing.
- Prose: complete sentences, characters as subjects, actions as verbs; no metadiscourse.
