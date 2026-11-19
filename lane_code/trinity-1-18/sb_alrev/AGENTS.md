# agent_project_distill — AGENTS.md

This repository holds the distillation stack for the SPLIT paper: the teacher collector (a fork of the sealed r1313 package), ground-truth adapters, materialization wrappers, the converter, the dataset builder, student trainers and the RGB-only evaluation harness. Data and run roots stay on `/data2/jjyeung/agent_project_data/` and never enter git.

The main repository `/home/jjyeung/agent_project` remains the authority for benchmark scoring (`AGENTS.md` §3) and the experiment request queue (`agent/agentic_information_5.0/EXPERIMENT_REQUEST_QUEUE.md`). Its `AGENTS.md` rules on legality (§7), answer banks (§7.0a), no deletion, and coordination (`.coord`) apply here too.

## Provenance

Code here is fixed in place and committed frequently. Every run, trace and target records the commit SHA and config hash, launches refuse a dirty tree, and code changes take effect at run-epoch boundaries. Only a change that touches admission, legality or scoring needs an independent review, and one review suffices. The main repository's immutable-round convention applies only to its benchmark-scored packages.

The running collector launches from `collector/` of this working tree, and its workers verify those bytes against the sealed contract at every spawn. Never change `collector/` on `main` while a collector runs from it. Land a fix on a branch, seal the new contract from an immutable epoch checkout under `/home/jjyeung/agent_project_distill_epochs/<commit>`, bind, drain, then fast-forward `main` and relaunch, in that order.

Lanes never switch or create branches in this working tree. Branch work happens in a separate `git worktree` under the lane's `work/` directory, and the orchestrator lands it on `main` by fast-forward. Untracked files count as dirty for `tools/provenance.py`, and a dirty or switched tree fails every collector gate that runs at that moment.

## Gates

A lane's suite gate covers the tests that exercise the code it changed plus its own new tests. Pre-existing failures or errors elsewhere go into the report with their cause and do not block a paid run or a launch. A strict source gate disposes of each source individually: valid sources proceed, invalid ones are recorded as deferred with the reason, and the denominator keeps them.

`docs/VERIFICATION.md` holds the verification recipes for `student/compact_targets` and `tools/gtmeasure`.

## Build experiments first (USER 2026-11-09)

Tokens are cheap, and GPU hours take wall-clock time, so build the code and kit for every candidate experiment as soon as it is proposed, before GPUs free up. Writing and debugging a whole experiment takes minutes, so a run never waits on its own code. Keep a ranked queue of ready-to-launch experiments, so any free GPU is filled within minutes. While runs train, read their code and data for bugs and fix them for the next launch, rather than discovering errors at launch. Before a new data receipt reaches GPUs, run every rank's first batch through the full forward pass on CPU. Build, test and debug anything that can run concurrently in parallel.

## code-aws jobs

The user's other project on the same account (job families a15_cot_c1159, c1164, c1167, c1171, c1173, c1175 and the cot_faithfulness workdirs) has priority on code-aws, and its orchestrator's requests bind this project at once. This project, distillation and main together, may hold at most 32 GPUs there, counting running and pending jobs, and submits no new job unless that orchestrator's limit allows it; requests arrive in `/home/jyeung/peer_inbox/TO_AGENT_PROJECT.md` on code-aws, which the main orchestrator watches and forwards. Distillation asks the main orchestrator before using any of the 32.

Every project job is named `a15_cot_ap` followed by an opaque random token with no further underscore, for example `a15_cot_ap7f3c9e21`, so the other project's admission check counts it as this project's. No job name, comment, workdir, path, argument, environment variable or log name may identify the project or its work: never the word "split" in any case, and no benchmark, dataset, model or method word such as revsi, vsibench, distill or qgen. Each lane records which run every opaque name belongs to in a ledger on Trinity, never on AWS; distillation's ledger is `lanes/aws_reserve/AWS_JOB_LEDGER.jsonl` under the data root. The Gemini key never goes to AWS.

## Searches and model settings

Search for files with specific patterns inside bounded directories. Sweeping searches over the file system have crashed many nodes, so give the same instruction to every subagent you launch.

An agent and all its lanes combined make fewer than two ssh invocations per minute into Trinity nodes, counting Trinity jump hosts such as trinity.vision.cs.cmu.edu; ssh from Trinity out to Orchard or AWS may be more frequent. Every ssh into Trinity goes through the shared rate limiter `lanes/tools/trinity_ssh.sh` under the data root, which allows one call per rolling 60 s per host it runs on, and Trinity-side state is read from shared files wherever possible. Reach Orchard directly from the lane's own host rather than through another Trinity node. Routine polling that touches any Trinity node runs at most once every 10 minutes, as one batched command; launch actions are batched into the same calls. Reuse existing ssh masters, never pass `-F` or `ControlPath=none`, and never write reconnect loops. Every ssh carries `timeout` and `-o ConnectTimeout`.

Gemini output budget: 32,768.

---

## Key Trinity Cluster Rules

Eliminate all pleasantries, no big or long paragraphs, be concise and short.
Trinity cluster: /data* and /home are overloaded network storage. Minimize reads/writes there; train and process from node-local /scratch (per-node, keep 100-200 GB free).
No recursive grep/find/du/ls -R, repeated big-file reads, or parallel IO on /data*. No >40K files in one directory.
Ask before any heavy IO command.
Max 2 nodes (or 16 GPUs) at normal priority; beyond that use vnice.sh. Run long jobs in tmux. Never run compute on the head node.

### 1. Confirm the destination uses InfiniBand.
ip route get <DESTINATION_IB_IP>
# Must show: dev ib0

### 2. Copy directly between nodes using their InfiniBand IPs.
rsync -avh --info=progress2 \
  -e "ssh -o BindAddress=<SOURCE_IB_IP>" \
  /scratch/source/ \
  username@<DESTINATION_IB_IP>:/scratch/destination/

---## Key Trinity Cluster Rules (Trinity admins, 2026-10-26)

_Copied verbatim from `/home/jjyeung/agent_project/AGENTS.md` (the Trinity admins' rules, USER 2026-10-26); keep this copy identical to that source._

These rules win over any other instruction an agent receives here (briefs, skills, scripts,
`agent/docs/`, `agent/scripts/DISPATCH_BOILERPLATE.md`) that would load the cluster more. They grant
no new permission: the §0.5 no-deletion rule still holds, so queue any `/data*` deletion for the
user. The sections after the **Agents** block carry the admins' rules file; replace them whole when
the admins publish a new version.

Eliminate all pleasantries, no big or long paragraphs, be concise and short.

**Agents:**
- Launch agents only on compute nodes (`trinity-<r>-<n>`), never on the head node `trinity`. An
  agent whose `hostname -s` prints `trinity` stops and tells the user.
- Never use an agent to SSH into Trinity: no agent outside the cluster (a laptop, Mind, Babel)
  opens an SSH, `scp` or `rsync` connection to a Trinity host, and no agent opens one to the head
  node. Agent SSH between compute nodes stays within the SSH limits below.
- Every agent runs with these rules loaded; a brief for an agent outside this repo carries this
  section.
- Users are accountable for every slowdown their agents cause.
- The admins enforce a three-violation rule: a first offense earns a warning, a second ends the
  user's agent use on Trinity, and a third bars the user from Trinity until after RSS.
- Ask before any heavy IO command. Heavy IO, and any rerun of work the cluster killed, waits for
  the user's answer; neither runs on a question's timeout default or under a relaunch loop.

You reach Trinity from a local machine: `ssh trinity` is the head node (trinity.vision.cs.cmu.edu), and `ssh trinity-X-Y` is a compute node, reached by jumping through the head node. Two shared chokepoints serve every user on about 20 nodes. One is the head node's two 1 Gb links (about 117 MB/s each). The other is **nebby**, a single NFS server on spinning disks that holds `/home`, `/data`, `/data2` and `/data3`. nebby has 16 worker threads and saturates at about 80 MB/s of total traffic, less when the traffic is small files. Most slowdowns come from one user overloading one of the two.

**Hard limit: 20 MB/s per user, summed over every node (USER 2026-11-08).** That covers everything you read from or write to `/home` and `/data*` and everything you send through the head node. Writes to `/home` and `/data*` count double, because nebby's disks are nearly full. Anything above the limit for a minute is killed, and repeat offenders are locked out of the cluster for a while. Copies between nodes over InfiniBand don't count toward the limit (see "Moving data").

### If something gets killed, stop
- If a job, copy or ssh connection is killed or drops unexpectedly, don't retry it, rerun it in a loop or look for a way around these rules. Repeated violations lock the user out of every node, which also cuts off their agents, scripts and VS Code/Cursor sessions.
- Tell the user what happened and which rule it probably broke. Then redo the work following this file.

### The head node is a doorway only
- Run nothing there except `ssh` hops. That rules out compute, Python, builds, `pip`/`conda`, `find`/`du`/`grep -r`, Jupyter and TensorBoard.
- VS Code and Cursor servers and `claude`/`codex` processes on the head node are killed automatically. Run agents only on a compute node.

### SSH: open few connections and reuse them
- Every new login runs startup scripts and reads your home directory from nebby, so it loads both chokepoints. Never run `ssh node cmd` once per file, per job or per status check.
- Stay within these limits:
  - At most 4 sessions open per node at once (6 on the head node), and 12 across the cluster.
  - At most 6 new logins a minute per node (10 on the head node), and 20 across the cluster.
- Reuse connections, so an agent holds one session per node however many commands it runs. Put this in your **local** `~/.ssh/config`:
  ```
  Host trinity trinity-*
      ControlMaster auto
      ControlPath ~/.ssh/cm-%C
      ControlPersist 30m
  ```
  `ssh -O check trinity-X-Y` should print `Master running`. Windows' built-in OpenSSH can't do this. Use WSL, or keep one session open in tmux on the node and work there.
- Keep `ProxyJump` in your laptop's config only. If `~/.ssh/config` on the cluster jumps through `trinity`, node-to-node copies go through the head node.
- Send a batch of commands as one `ssh node 'bash -s' < script.sh`. Check job status at most once a minute. Run long jobs in `tmux` on the node.
- Use one VS Code/Cursor window per node.
- If a command hangs (usually nebby stalling), don't retry it in a loop. Wait, or tell the user.

### Moving data
Throttle every copy to these rates. Your 20 MB/s is shared by everything you run on every node. Run one copy at a time, and don't run one while your jobs are reading `/data*`. For more than about 30 GB through `/data*` or the head node, plan it with an admin.

| Path | Rate | Per hour |
|---|---|---|
| Reading from `/home` or `/data*` | 8 MB/s (`rsync --bwlimit=8000`) | ~30 GB |
| Writing to `/home` or `/data*` | 4 MB/s (`rsync --bwlimit=4000`) | ~15 GB |
| Internet or laptop to or from the cluster | 8 MB/s | ~30 GB |
| Node to node over InfiniBand (tar pipe) | 300+ MB/s, no limit | 1 TB+ |

- **Move archives, never folders, to or from `/home` and `/data*`.**
  - Never use `scp -r`, `rsync -a`/`-r`, `cp -r`/`-a`, `rclone copy`/`sync`, `aws s3 sync`, `gsutil cp -r`, `hf upload` or `wget -r` there. Copy archives with plain `rsync --bwlimit=...`, without `-a` or `-r`, even for a single file.
  - Never extract into `/home` or `/data*`. Extract on `/scratch`.
- **Don't run copies in parallel or one per file.** No `xargs -P`, `parallel`, `find -exec`, or loops of `scp`/`cp`/`rsync` on `/home` or `/data*`. Keep it to well under 60 copy commands a minute.
- **Archives from `/data*` onto a node:** use one command for all files:
  `rsync --bwlimit=8000 --partial /data3/shared/datasets/foo/*.tgz /scratch/$USER/foo/`
  Then extract them in `/scratch/$USER/foo`.
- **A folder on `/data*` that isn't archived:** stream it once, throttled, straight into `/scratch`:
  `cd /scratch/$USER && tar cf - -C /data3/path ds | pv -q -L 8m | tar xf -`
- **Node to node:** copy directly over InfiniBand. `.ib` hostnames are about 100x faster than the plain names, which use 1 Gb Ethernet. Use this tar pipe, not `rsync` or `scp`, which count toward your 20 MB/s even between nodes:
  `ssh trinity-A 'cd /scratch/$USER && tar cf - data | ssh trinity-B.ib "cd /scratch/$USER && tar xf -"'`
- **Many nodes need the same data:** pull it from `/data*` onto one node, then copy node to node. Each finished node can feed the next. Never pull the same data from `/data*` on several nodes at once. On Oct 25, five nodes copying one dataset took three quarters of nebby.
- **Results into `/data*`:** archive them on `/scratch`, then copy the archive:
  `rsync --bwlimit=4000 --partial /scratch/$USER/out.tgz /data3/$USER/`
- **Laptop to or from a node:** archive on the node first, then run this from the laptop:
  `rsync --bwlimit=8000 --partial trinity-X-Y:/scratch/$USER/out.tgz .`
  The `scp` equivalent is `scp -l 64000`.
- **Never relay through the head node or your laptop.** Don't use `scp -3`, don't `rsync` between two nodes from your laptop, and don't pipe `ssh A | ssh B` on your laptop. Each of these sends every byte across the head node's links up to four times. That was the main cause of the head-node slowdowns on Oct 23 and 24.
- **Internet downloads** (Hugging Face, pip, datasets) all pass through the head node. Download once, on one node, into `/scratch`, throttled:
  - `wget --limit-rate=8m`, `curl -L --limit-rate 8M`, `rclone --bwlimit 8M`, or `aws configure set default.s3.max_bandwidth 8MB/s`.
  - `hf download` can't be throttled. Fetch big files with curl instead:
    `curl -L --limit-rate 8M -H "Authorization: Bearer $HF_TOKEN" -o FILE https://huggingface.co/ORG/REPO/resolve/main/FILE`
    Datasets use `https://huggingface.co/datasets/ORG/REPO/resolve/main/FILE`.

### Work from /scratch, not /home or /data*
- `/scratch/$USER` is the node's local disk. Keep your code (a git clone), environments, caches, data, checkpoints and logs there. `cd` into it before starting jobs and loops.
- Point caches at `/scratch`, in job scripts or `~/.bashrc`. By default they live in `/home`:
  ```
  export XDG_CACHE_HOME=/scratch/$USER/.cache HF_HOME=/scratch/$USER/hf \
         TRITON_CACHE_DIR=/scratch/$USER/.triton CONDA_PKGS_DIRS=/scratch/$USER/conda-pkgs
  ```
- Create conda or venv environments under `/scratch/$USER/envs` on one node. Copy them to other nodes with the tar pipe; the path is the same on every node, so they work as-is. Don't install into `/home`. Installs there are thousands of small-file writes, and every Python start reads them back from nebby.
- Read training data from `/scratch` only. A job reading `/data*` counts toward your 20 MB/s and gets killed when it goes over. Dataloader workers reading small files from `/data*` also stall nebby for everyone.
- Write checkpoints and logs to `/scratch`. Writing a large checkpoint straight to `/data*` goes over the limit and kills the training job. Copy only the checkpoints you need to keep into `/dataX/$USER`, once, at the end.
- Avoid anything that touches many files on `/home` or `/data*`. That means `find`, `du`, `ls -R`, `grep -r`, `git status` on big trees, `pip install`/`conda create`, editor indexing, and programs that keep many threads waiting on NFS or open hundreds of files there a minute. Never run them on several nodes in parallel.
- Keep data on `/data*` as a few large archives, not as folders of small files. Never put more than 40K files in one directory.
- nebby's pools are 97–99.5% full. Delete what you no longer need from `/data*`, and don't make your own copy of a shared dataset there.
- Leave 100–200 GB free on `/scratch`. It shares a disk with the OS. Anything on `/scratch` that you need on another machine has to be copied off.

### Sharing compute
- There is no scheduler. Check http://trinity.vision.cs.cmu.edu:53240/ before picking a node. Use at most 2 nodes or 16 GPUs at normal priority, and run anything beyond that under `vnice.sh` (`/data3/shared/scripts/vnice`).
- Don't hold idle GPUs with "keeper" scripts.

## Git on Trinity: necessary work only

**Subagents default to no Git commands.** Git can overload Trinity nodes, especially
in the large `agent_project` repository. This rule applies locally and over SSH on
every Trinity node. Use Git only when the task genuinely requires it, and assign one
owner to serialize the necessary, narrowly scoped operations. Do not run routine
`git status`, `diff`, `log`, worktree inventories, recursive untracked scans, or
Git-backed checkpoint checks at startup, after each edit, or during monitoring.
Other workers continue edits and tests without Git. Validate edits with bounded
file reads and batch required checkpoints through the designated Git owner.
This rule governs all startup and checkpoint procedures in these instructions.

## Prose style (Williams, *Style: Lessons in Clarity and Grace*)

Apply to all prose written for a human reader — chat responses, summaries, commit
messages, docs, comments. These govern sentence architecture, not length; they are not a
mandate to be terser, and they never justify fragments, arrow chains, or dropped articles.

- Make the main character the grammatical subject and its key action the main verb.
  "An evaluation was conducted" -> "I evaluated the checkpoint".
- Unpack nominalizations sitting next to a limp verb (`-tion/-ment/-ance/-ity` beside
  *is / has / perform / conduct / result in*). "results in an improvement of" -> "improves".
- Open a sentence on old information and end it on new. Consecutive sentences should share
  a topic thread rather than each starting somewhere different.
- Put what you want remembered at the end of the sentence, not buried in the middle.
- State a paragraph's point in its first sentence; the rest supports it.
- Delete metadiscourse: "it is important to note that", "it should be pointed out that".

Full treatment: `~/paper-writing/style-summaries/MASTER_CHEATSHEET.md`. The book itself is
at `~/paper-writing/Style - Lessons in Clarity and Grace.pdf` (covers through Lesson 3).

## Current state only (no-archaeology)

Text you write for agents (instruction files, skills, memory, briefs) states the current rule
only: rewrite an old ruling into the new one instead of appending, keep at most one date stamp,
give the reason in one timeless clause, and never narrate superseded rulings or incidents. Apply
it to the text you are writing or the files you were asked to edit, never as a sweep of others.

## Questions never block (USER 2026-10-22)

Never wait on the user, in any project. Ask in plain text instead of the blocking question tool,
send a PushNotification, and record the question with its default in the project's saved-questions
file (`/data2/jjyeung/agent_project_data/SAVED_USER_QUESTIONS.md` for agent_project and its sibling
repos). Keep working; after about 5 minutes without an answer, act on the default (rerun failed
work, or collect the superset of the data) and tell the user afterwards. The saved-questions file
holds only unanswered rows: move an answered row to `SAVED_USER_QUESTIONS_ANSWERED.md` in the same
folder with the answer and `Answered by` set to `USER` (the user answered in any session) or `AGENT`
(an orchestrator, another agent or evidence settled it). Ask each question once: never repeat open
questions in later replies or status updates, and list them again only when the user asks whether
there are questions (USER 2026-11-07). Only work that needs a paid key the user gates (NV inference or
OpenRouter) waits for an answer.

## Context-efficient file reading

- For large files, search first and then use `Read` with `file_path`, `offset`, and `limit` to fetch only the relevant lines.
- Do not read an entire large file unless full-file understanding is necessary.
- Do not reread content already available in the conversation.

## Paper repo (`/home/jjyeung/agent-project-paper`)

Coauthors see the paper only on Overleaf. Pull with `git pull --rebase overleaf-eccv main`
before editing. After every validated paper edit, commit and run
`git push overleaf-eccv HEAD:main`; this is standing authorization for that push. A paper edit
that is only committed locally is not finished. The paper repo's `AGENTS.md` holds the full rule.

## Stopping other agents' work (USER 2026-10-29)

Whenever you stop work that another agent started (a lane, an orchestrator, a subagent, a service or a job), tell the orchestrators right away: what you stopped, where, why, and that they can restart it whenever they choose. Append one line to `/data3/jjyeung/orch_n13_20261026/STOP_NOTICES.md` (`<UTC time> <who you are>: I stopped <what> on <host> because <why>; restart it whenever you want.`), or message the orchestrator session directly. Never use `lanemsg tell all`; it scans a large NFS registry and opens SSH logins to every old lane host.

## Subagent tiers and effort (USER 2026-11-08)

Give every subagent the model tier and the reasoning effort its task needs, including each `agent()`
call inside a workflow. Never let a subagent inherit the orchestrator's model or effort: the user sets
the orchestrator's effort for the orchestrator alone. Sonnet does mechanical reads, lookups,
inventories and extraction at low or medium effort; Opus does builds and launches at high,
babysitting at medium, and judgment-heavy reading and refute verifiers at high; Fable does only the
hardest synthesis or ruling, or a run that has already failed repeatedly, at high or xhigh. Use max
for debugging, for designing experiments, and whenever the user asks for it; elsewhere pick the
lowest effort that does the task well. Use a workflow only when a task needs a real multi-agent
fan-out; otherwise spawn one agent. Set `model:` and `effort:` explicitly on every spawn, and choose
the matching effort for Codex and Devin lanes (Codex mode or reasoning effort, Devin model variant).

## Design records (USER 2026-11-08)

Every design, debugging or research agent saves what it learned, so no later agent pays to explore the
same path twice. A record holds the question, the answer, the reasons with evidence, every option
considered and rejected with the reason, what might not work and how we would notice, the tests that
would settle it, and the status. Give each brief the record's path, and read the project's record index
before starting such a task. Distillation records live in `/data2/jjyeung/agent_project_data/distill_design/`
(one file per topic, listed in `INDEX.md`), not on `/scratch`, which is cleared after 7 days.
