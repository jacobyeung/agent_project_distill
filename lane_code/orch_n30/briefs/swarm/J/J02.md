# J02: literature sweep since 2026-11-01 for spatial video-language models up to about 13B, with every bar verified at its source

Read /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/briefs/swarm/SWARM_RULES.md first. It binds you, and so does the file it names first (LANE_RULES.md, which names the cluster rules in /home/jjyeung/.claude/CLAUDE.md). Where LANE_RULES and SWARM_RULES differ on reporting or folders, SWARM_RULES wins: no events, no STATUS.md copies, no D/INDEX.md lines; deliver only to R.

Task id: J02. Task directory: /scratch/jjyeung/swarm_20261120/work/J02 (create it).
Carrier: Codex (gpt-6-astra), effort max. Host: trinity-3-30. Run `hostname -s` first; if it prints anything other than trinity-3-30, write that as the first line of your result file and stop.
Network (this brief names this stream): search and read public pages (arXiv listings, abstracts and HTML, papers, project pages, Hugging Face model cards, GitHub READMEs, official benchmark leaderboards); each download under 20 MB, one at a time, never a dataset, checkpoint or benchmark item file, never `git clone`. Save what you cite under S/work/J02/sources/ and record URL and sha256 in R/files/J02/SOURCES.tsv.
Abbreviations: B = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30, D = /data2/jjyeung/agent_project_data/distill_design, R = /data2/jjyeung/agent_project_data/distill_design/swarm_20261120, S = /scratch/jjyeung/swarm_20261120, M = /home/jjyeung/.claude/projects/-scratch-jjyeung-orch-home-distill/memory.

## Goal and why
Find every spatial video-language model up to about 13B published or updated since 2026-11-01 and every new number on ReVSI, VSTI-Bench and VSI-Bench, verify each number at its primary source, and deliver the updated table of bars we must beat plus three methods worth testing, each with its smallest test. Our claim is that a ~9B model whose chain of thought calls its own heads beats the open models, so a stale bar either hides a target we already missed or wastes GPU-hours chasing one that moved.

## Inputs (read-only)
1. Our recorded bars: M/sota-bars-9b-20261109.md (GeoWeaver-10B 75.05 VSI-Bench and 57.5 ReVSI; Cambrian-P 73.7 at 128 frames; SpatialAxiom unverified), M/closed-model-bars-20261111.md, M/reference-qwen3d-arxiv-2608-02980.md, D/SOTA_TARGETS_20261108.md, D/SOTA_SURVEY_GEOMETRY_VLMS_20261109.md, D/FRONTIER_READ_20261111.md, D/OTHER_METHODS_TRACE_ANALYSIS_20261119.md.
2. Our own numbers, for context only (never compare across protocols without saying so): M/result-revsi-direct-step544-20261115.md, M/result-official-vsi-direct-step544-20261115.md, M/result-vsti-native-camera-step544-20261116.md.
3. Rulings that constrain the methods you propose: M/no-harness-end-to-end.md, M/uniqueness-not-replication.md, M/drastic-architecture-ok-20261109.md, M/user-ruling-sam3-tower-own-encoder-20261110.md, M/revsi-focus-64-frames-20261116.md, M/no-licence-restrictions.md.

## Question
Which spatial video-language models up to about 13B appeared or were updated since 2026-11-01; what do they report on ReVSI, VSTI-Bench and VSI-Bench and under which protocol (frames, resolution, chain of thought or not, VSI-Bench original or debiased, ReVSI version, VSTI original or the corrected 5,736-item set); do the recorded bars still stand; and which new methods are worth testing in our design?

## Method
1. Sweep arXiv (cs.CV, cs.CL, cs.RO listings and search) from 2026-11-01 to today, the benchmarks' official pages and leaderboards, and the model cards and READMEs those lead to. Also re-check the recorded bars (GeoWeaver-10B, Cambrian-P, SpatialAxiom) for revisions.
2. For every number, open its primary source (the paper's table or the official leaderboard) and record table or figure number, URL, version or date, and protocol. A number you cannot open at its source is UNVERIFIED and stays out of the bar.
3. Build R/files/J02/BARS.md: model, size, date, VSI-Bench, ReVSI, VSTI-Bench (each with protocol), source, verified (yes or no), and whether it is comparable with our reads as recorded (frames and protocol); then the current open bar per benchmark at about 9B and at up to 13B, and the closed bars if any changed.
4. Write R/files/J02/METHODS.md: three methods from the sweep worth testing inside our end-to-end, own-heads design, each with the mechanism, the paper's evidence (table and number), what our records already measured nearby (cite D or M), the smallest test (CPU first, else the fewest GPU-hours, on which development set, with which bar), and the rulings it must respect.

## What counts as a finding
A bar that changed, a new model above a recorded bar, or a recorded bar that does not hold at its source, each with its verified citation. CONFIRMED means you opened the primary source; SUSPECTED means a secondary source only.

## Out of scope
Benchmark items or answers, downloading models or data, GPU, and editing code.

## Deliver (per SWARM_RULES; create the R folders with `mkdir -p` if they are missing)
- /data2/jjyeung/agent_project_data/distill_design/swarm_20261120/results/J02.md, at most 60 lines: changed or new bars first, each with its verified source; the bar table summary; the three methods with their smallest tests; then what you did not cover.
- /data2/jjyeung/agent_project_data/distill_design/swarm_20261120/files/J02/: BARS.md, METHODS.md, SOURCES.tsv. At most 30 files, each under 5 MB.
- One line appended to /data2/jjyeung/agent_project_data/distill_design/swarm_20261120/DONE.txt: `<date -u +%Y%m%dT%H%MZ> J02 <CONFIRMED count> <SUSPECTED count> <one-line headline>`.
If your sandbox refuses writes under R, write the same files under S/work/J02/deliver/ with the same names and say so in the first line of your final message.

## Cutoff
The credit that pays for you ends tonight. Write the results file within 30 minutes (even if it only lists what you have so far) and update it as you go, most valuable finding first. Assume you can be cut off at any moment after 2026-11-21T07:00Z (23:00 PT); whatever is not on disk under R by then is lost. Budget: 90 minutes.
