# Rules for every distillation lane (orchestrator on trinity-3-30; tools in /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30)

Read `/home/jjyeung/.claude/CLAUDE.md`, section "Key Trinity Cluster Rules", first. Those rules win over this file and your brief.

## Where you are
- You run on one Trinity compute node; your brief names it. Your working directory is the repository root on /home only because Devin needs a trusted folder: do not search, list or read it. Work in your lane folder `/scratch/jjyeung/orch_n30/<lane>` (node-local) by absolute path, under 2 GB unless the brief says more; check `df -h /scratch` before any write above 1 GB.
- trinity-2-18 and trinity-2-28 are unreachable. Every path under `/scratch/jjyeung/orch_cd/` or `/scratch/jjyeung/orch_n28/` is on them and cannot be read. Never ssh to them, never wait for them.

## Forbidden
- No recursive grep/find/du/ls -R or built-in search tool on /home or /data*: read named files, list single directories, read big files in bounded parts.
- No Git command. No deletion or overwrite outside your lane folder; list removal candidates in `<lane>/REMOVAL_CANDIDATES.md`.
- No copy to or from /home or /data*, and no transfer across the head node (internet, GCS, Orchard), except a stream your brief or an orchestrator note names. Every such stream above 20 MB registers with the IO governor (serial-v1 on trinity-3-30) before it moves a byte: read `/data3/jjyeung/orch_n13_20261026/io_governor/README.md` and follow it exactly. In short: the stream's host needs a live node agent (README section "Node agent"; first check `tmux has-session -t iogov_agent` and the "Node agents" line of STATE.md, and start one only if none runs on your node); the data path holds `ratelimit.py` (helpers in README step 1); one archive from /data* uses `launch_paced_archive.py`, one archive into /data* uses `copy_archive.py`, any other pipeline (a tar stream of a file list, a `gsutil cat`, a `curl`, an ssh pull) starts stopped and registers with `register.py --tier 3 --allow-resume` (`--writes-nfs` when it writes NFS; `--io-weight 1` for a pure internet or head-node transfer); then wait for `running` in STATE.md and rename the record to `.done.<epoch>` when the copy has finished. The governor admits one stream at a time for the whole account and orders by tier, priority, then registration time, so register ALL the streams your step needs at once (each pipeline started stopped, each with its own record and the priority number the orchestrator gave you) instead of one after another: a stream registered late waits behind every stream registered before it, the mover's multi-gigabyte archive parts included. Expect to wait. `pv`-paced pipelines and `rsync --bwlimit` hand copies are not admitted any more; the outage hand procedure and REGISTER.md lines have ended. A single file under 20 MB (a record, a manifest, a code tar) may move unregistered, one at a time, never in a loop.
- No GPU use unless your brief authorizes it. Never trinity-0-8, 0-23, 3-23; nothing on trinity-0-18.
- No Gemini, OpenRouter or NV call.
- If a job, copy or ssh is killed or hangs, do not retry: write a BLOCKER event naming the rule it probably broke.

## SSH
- Into Trinity: under 2 ssh calls a minute in total, each with `timeout` and `-o ConnectTimeout=20`, batched as `ssh node 'bash -s' < script`. Long work in `tmux` on the target node; poll once a minute at first, then every 5-10 minutes. Never `-F`, `ControlPath=none`, or a reconnect loop. Nothing on the head node `trinity`.
- Orchard: only `timeout 300 bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh 'bash -s' < script.sh` (shared connection per node; plain `ssh orchard` calls time out). One failure: wait 2 minutes, retry once; a second failure is a BLOCKER. Query Slurm with `TZ=UTC`. Orchard job names are `a15_cot_ap` + opaque hex; no project, benchmark, dataset, model or method word anywhere on Orchard; record token meanings in `<lane>/work/ORCHARD_LEDGER.jsonl` on your node.

## GPU launches (only when authorized)
Two fresh `nvidia-smi` readings 5+ minutes apart showing the card empty, recorded in the launch event. Off trinity-0-13 run under `/data3/shared/scripts/vnice/vnice.sh`; work vnice kills is not rerun without the orchestrator's order. After any launch check liveness and output every minute, lengthen to 10 minutes once output lands, back to 1 minute on regression. Read data from /scratch only; write results to /scratch.

## Builders and reviews
Code builds go to Codex: `(cd /home/jjyeung/agent_project_distill && agent/scripts/codex_dispatch.sh implement <dir on /scratch> <prompt file> --model gpt-6-astra --effort high --label NAME --skip-git-check)`; one only when a launch or decision needs it, with a complete brief; never ask it to ssh or kill. You do not review your own work for a launch gate: ask for the review in a RESULT event.

## Reporting
- Events are the only channel: write `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/<lane>/<UTC stamp>_<RESULT|QUESTION|BLOCKER>_<slug>.md`, at most 20 lines, stamp from `date -u +%Y%m%dT%H%MZ` in the writing command; detail goes in files the event names. Event only for a result, question or blocker. Answers arrive in `<lane>/inbox/` on your node and as `<UTC>_ORCH_*.md` in that events folder; read both at each step.
- A question never blocks: state your default in the event and continue on it.
- Keep `<lane>/STATUS.md` current after every step and copy it to the events folder as `STATUS.md` (a successor resumes from it alone).
- Do not end your turn while work is owed; wait with `sleep` of at most 10 minutes. Near 300K tokens finish the step, update STATUS.md and write a RESULT event `rotate`.
- Findings go in a record under `/data2/jjyeung/agent_project_data/distill_design/` plus one INDEX.md line: question, answer, evidence, options rejected and why, what might not work and how we notice, tests that would settle it, status.
- Nothing you build may exist on one node only: when a kit is sealed, a packet accepted or a dataset complete, tar it and copy over InfiniBand to a second node's `/scratch/jjyeung/n30_mirror/<lane>/` (`tar cf - X | ssh -o ConnectTimeout=20 <node>.ib '...tar xf -'`), compare sha256, record both paths in STATUS.md. Above 5 GB ask first. Orchard-resident material needs no mirror if STATUS.md records path and sha256.
- Times to the user in PT; stamps in UTC. Report failures with their output; never report a check you did not run.
- A registered stream keeps its registered process: the root PID of a governed pipeline never `exec`s another program (run the worker as a child and wait for it), because the governor re-checks the PID's command name at every admission and refuses a record whose name changed after a pause.
