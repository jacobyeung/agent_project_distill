# Codex build 23d of lane tree_rebuild: fix review 23c's two MUSTs in the kit GPU guard diagnostic (kit-only), on top of build 23c

You run once, on trinity-1-18; nobody answers questions. Writable workspace `L=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w23` only. Continue in it, keep every existing package unchanged, and move superseded files to `L/attic/`. Binding prompts: `/scratch/jjyeung/orch_n30/tree_rebuild10_w/prompts/build23c.md` and the prompts it names (rules hold). Base: build 23c (`out/tree_rebuild_b23c_db042c7c.tar`, tree 5b349b18 unchanged, kit q a258d7e7, report `out/BUILD23C_REPORT.md`). Time limit: package by 15:45Z 2026-11-19; the counting proof is submitted the moment you finish. Keep the change minimal. A CPU capacity replay of build 23b is running in this workspace (`work/build23b/`, tmux tr13_cap23b); do not touch `work/build23b/`.

## Findings (review 23c, `/home/jjyeung/agent_project_distill/agent/scratch/codex_runs/` newest `*_tree_rebuild_rev23c/final_message.md`)
1. MUST: `work/build21/kits/q/b/g.py:11` reads `torch.__version__` outside the exception handler; with that attribute absent the guard raised AttributeError with no diagnostic and no E42.
2. MUST: the diagnostic prints `CUDA_VISIBLE_DEVICES` verbatim, and arbitrary environment text passes through `b/z.py:284 screen()`.

## Do
1. Change the generator (`work/build21/kit.py`) and the emitted `q/b/g.py`. Every value the diagnostic reads is read inside the handler, and any exception still prints the diagnostic and refuses E42. Do not print CUDA_VISIBLE_DEVICES; print only whether it is set and the number of comma-separated entries. The device name is printed only if it matches `^[A-Za-z0-9 ._-]{1,64}$`, else as `"?"`. The decision logic is unchanged: refuse unless CUDA is available, at least 1 device, memory known and at least 75 GiB.
2. Tests: the reviewer's two cases (attribute absent -> diagnostic + E42; a CUDA_VISIBLE_DEVICES of `/tmp/private-project/model/secret-DEMO` never appears in the output) fail before and pass after; keep 23c's 9 guard tests passing; decoded scan PASS; kit/naming/resolver suites.
3. Regenerate and reseal kit q. Write `out/UPLOADS_NEW_23D.json` (list of {name, bytes, sha256, local_path} versus kit q a258d7e7). Update `out/GUARD_PATCH.md` / `GUARD_PATCH.diff` for build 24. Package `out/tree_rebuild_b23d_<seal8>.tar`; `out/BUILD23D_REPORT.md` under 25 lines.

## Rules (restating build 21's)
No ssh, network, Orchard, GPU, Git, tmux, scheduler or other agents. Never list, search or grep on /home or /data*: read only the named file there. Write only under L. No deletion. Every CPU process runs under `nice -n 10` with at most 8 threads, under 20 GB RAM. The tree, config, resolver identities, admission, legality and the DEFERRED boundary do not change. GO stays false.
