## Standing rules and answers (read first; you will get no replies, so do not wait for any)
- You run on trinity-1-18 (CMU Trinity cluster), CPU only, no GPU, no network. Never ssh, never kill a process, never touch tmux sessions, no Git, no deletion outside your workspace.
- /home and /data* are an overloaded NFS server: never search, list recursively or bulk-read there. Read only files this prompt names, each once. /scratch is local disk: bounded `rg --files`/`find` under the directories named here is fine.
- Write only inside your workspace. Every path outside it that this prompt names is read-only to you (other lanes own it).
- Local-disk IO needs no approval. Ordinary failures: debug and rerun. The sandbox has no loopback sockets. Stay under 40 GB RAM per process; use at most 16 cores.
- Legality: never invent a mapping, a manifest, a scene list or a proof. A missing input is reported by its exact name and expected location; the affected output says MISSING, never a guess.
- Every output JSON records sha256 of each input it rests on, and your report states the command that produced each number. Write a STATUS.md in the workspace after each stage (one paragraph) and a final report named in the task.
