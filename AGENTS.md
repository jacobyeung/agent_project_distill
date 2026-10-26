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

---