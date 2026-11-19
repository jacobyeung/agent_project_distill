W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; free -g | sed -n 2p
cat > $W/prompts/build24g.md <<'EOPX'
# Codex build 24g of lane tree_rebuild: kit-only fix, the export copier must find the minted sessions file on /project, on top of build 24f

You run once, on trinity-1-18; nobody answers questions. Writable workspace `L=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24` only. Continue in it, keep every existing package unchanged, and move superseded files to `L/attic/`. Binding prompts: `/scratch/jjyeung/orch_n30/tree_rebuild10_w/prompts/build24f.md` and the prompts it names (rules hold). Base: build 24f (`out/tree_rebuild_b24f_449bc1fc.tar`, report `out/BUILD24F_REPORT.md`, tree 57a1f14d). Kit-only: the tree stays byte-identical (57a1f14d). Time limit: package within 30 minutes. Do not touch `work/build24f/rehearsal*` (a rehearsal is running there now) and do not run go_rehearsal.sh.

## Finding
`b/pc.py:57` sets `self.home = TK_KIT_HOME or <root>/h`. pc.py runs from job.sh's batch shell (b/pc.sh), where TK_KIT_HOME is unset; z.py sets it only for the child j.sh, and to the node-local `boot_node/'h'` (z.py:588). The copier therefore looks for `sess.json` in node-local `$N/h`, where nothing ever places it, so every export records "export not uploaded: no sessions" even after the sessions are minted. The minter (lane n_ops1, on Trinity) installs one file on Orchard by one small copy. It cannot go into the kit dir, because each kit dir must equal its SHA256SUMS plus BUILD.json and SHA256SUMS.txt.

## Do
1. In kits n and `out/kit_n_go` (and q only if q runs the copier; say which), the copier reads the sessions from a fixed /project path outside the kit dir: `<n_root>/n_s/sess.json` (n_root from k/p.json), unless an explicit argument names another path. Ignore TK_KIT_HOME for this. Before use, require the directory to be mode 0700 and owned by the job user, and the file to be a regular non-symlink file of mode 0600 that parses as a JSON object of part name to URL; otherwise record `export not uploaded: sessions unusable (<reason>)` without printing any value. Keep the node-local private copy (0600) as now. The names in `out/SESSION_NAMES_24F.json` stay the same; if they must change, write `out/SESSION_NAMES_24G.json` and say why.
2. Tests (failing before, passing after): with TK_KIT_HOME unset and a stand-in n_root holding n_s/sess.json (0700/0600) plus a stub writer, one export reaches its done marker; a wrong mode, a symlink, a missing file and a non-object file each record the named status and upload nothing; no session value appears in any log, live file or report.
3. Rerun the decoded scans, the kit/naming/resolver/guard/live suites and the copier tests. Reseal kits q, n and kit_n_go. Write `out/UPLOADS_24G.json`/`.list` (diff after 24f), `out/UPLOADS_24G_GO.json`, update `out/N_CARD_KIT_ROWS.md` (sessions path and modes), package `out/tree_rebuild_b24g_<seal8>.tar` with `out/DELIVERY_24G.json`, and write `out/BUILD24G_REPORT.md` under 25 lines.

## Rules (restating build 21's)
No ssh, network, Orchard, GPU, Git, tmux, scheduler or other agents. Never list, search or grep on /home or /data*: read only the named file there. Write only under L. No deletion. Every CPU process runs under `nice -n 10` with at most 8 threads, under 20 GB RAM. Do not change the tree, config, admission, legality, removals, opener rows, the step-544 lineage, the resolver identity checks or the DEFERRED boundary. GO stays false except in `out/kit_n_go`, which is not uploaded.
EOPX
sha256sum $W/prompts/build24g.md | cut -c1-16
tmux new -d -s tr14_b24g "cd /home/jjyeung/agent_project_distill && nice -n 10 agent/scripts/codex_dispatch.sh implement $W/w24 $W/prompts/build24g.md --model gpt-6-astra --effort high --label tree_rebuild24g --skip-git-check > $W/work/build24g_dispatch.log 2>&1"
sleep 15; tmux ls | grep tr14; tail -c 800 $W/w24/work/build24f/rehearsal_run.log
cat $W/w24/out/SESSION_NAMES_24F.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('parts',[])), sorted(d.keys()))"
