W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; C=$W/work/conf21c
cat > $W/prompts/build21d.md <<'EOP'
# Codex build 21d of lane tree_rebuild: close the two scanner gaps of review 21c (scanner only), then repackage

You run once, on trinity-1-18, and nobody answers questions while you run. Your whole writable workspace is `L=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21`. The prompts `/scratch/jjyeung/orch_n30/tree_rebuild10_w/prompts/build21.md` (facts, "Rules for the build") and `.../prompts/build21c.md` bind you; build 21c is DONE: package `out/tree_rebuild_b21c_6f5e6cc2.tar` (sha256 8c563434..., tree seal b262e7a7, kit q seal 93b4404f), report `out/BUILD21C_REPORT.md`. Keep that package unchanged; write the new one beside it. Time limit: package by 10:20Z 2026-11-19 (run `date -u` at each step); the production proof waits on you. Keep this build narrow.

## Review 21c (Codex, NO-GO, one MUST) — verbatim findings
"The extended scanner still misses forbidden names. Two in-memory mutations passed:
- Decoded-map bypass: naming21.py:63 exempts nested payload fields through the filters at lines 79 and 85. I decoded the first `k/s.json` entry, added `{"BeNcHmArK":"DaTaSeT"}`, recomputed both capsule hashes, and called `scan_decoded(kit)` with patched reads. Result: PASS, 66,500 checked strings.
- Environment-name bypass: naming21.py:112 checks only Python strings resembling paths. Appending `os.environ["BeNcHmArK"]="q"` to the in-memory `b/o.py` returned PASS. This environment mutation is absent from the build's tests."
The reviewer confirmed the original filename defect is fixed and found no actual forbidden name in the kit.

## Do, in order
1. Scanner (`work/build21/naming21.py` and, only if it holds the same logic, the job-side check in `joblib.py`): every map key and every string value in every decoded map (nested payloads included) is checked, except values inside an explicit, small, named allowlist of authenticated provenance fields (each listed field: why it must keep its original identifier, and that it is file content never used as a name, path, argument, environment entry or log line). Every environment name and value the kit's Python and shell set or pass (os.environ[...] =, os.environ.update, env= dicts, export / VAR= in shell, srun/sbatch --export) is checked, whether or not it looks like a path.
2. Tests: the two reviewer mutations above as failing-before tests (old scanner PASS, new scanner refuses by name), plus one mutation each for: a forbidden word as a nested map value, `export BeNcHmArK=1` in a kit shell file, an `env=` dict key in kit Python.
3. Run the new scanner on the final kit. If it finds a real forbidden name in a job-visible place, fix that place (opaque name, pinned map, content hash unchanged) and say so; otherwise the kit q bytes must stay byte-identical to build 21c's (state the kit seal before and after). Rerun the build-21 focused steps (`work/build21/focused.py`) and the naming/kit tests (kit21c, naming21c, extra21c and the new ones).
4. Package `out/tree_rebuild_b21d_<seal8>.tar` with updated manifest; `out/BUILD21D_REPORT.md` under 120 lines (changed files, allowlist with reasons, tests with counts, scan result, kit seal before/after, package sha256/bytes, upload bytes/files).

## Rules (restating build 21's)
No ssh, network, Orchard, GPU, Git, tmux, scheduler or other agents; never list, search or grep on /home or /data*; write only under L; no deletion (move superseded files to `L/attic/`); every CPU process under `nice -n 10` with at most 8 threads; no process above 20 GB RAM; L's growth under 2 GB. Do not change the sealed tree, P's trained opener rows, the step-544 lineage path, admission, legality or the DEFERRED component-evidence boundary; GO stays false.
EOP
sha256sum $W/prompts/build21d.md
tmux new -d -s tr12_b21d "cd /home/jjyeung/agent_project_distill && nice -n 10 agent/scripts/codex_dispatch.sh implement $W/w21 $W/prompts/build21d.md --model gpt-6-astra --effort high --label tree_rebuild21d --skip-git-check > $W/work/build21d_dispatch.log 2>&1"
tmux new -d -s tr12_ff21c "cd $C/pkg && nice -n 10 bash work/build21/run.sh work/build21/focused.py > $C/focused_untar2.log 2>&1; echo rc \$? >> $C/focused_untar2.log"
sleep 30; tmux ls | grep tr12; d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*tree_rebuild21d | head -1); echo $d; stat -c %s $d/transcript.log; tail -2 $C/focused_untar2.log
