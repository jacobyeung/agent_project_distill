# Codex build 21f of lane tree_rebuild: scanner-only fix for review 21e's MUST; kit q bytes must not change

You run once, on trinity-1-18; nobody answers questions. Writable workspace `L=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21` only. Binding prompts (read first): `/scratch/jjyeung/orch_n30/tree_rebuild10_w/prompts/build21.md` ("Rules for the build"), `build21d.md`, `build21e.md`. Build 21e is DONE (`out/BUILD21E_REPORT.md`, package `out/tree_rebuild_b21e_ac8fa8e3.tar`, kit q seal 5d300f192c97134c441696df0ab09435e2ad15be879603b230e6cd0c5d615522): keep it unchanged. Time limit: 11:25Z 2026-11-19.

## Review 21e (Codex, NO-GO, one MUST) — verbatim
"The scanner still misses a forbidden environment name. naming21.py:69 skips tuple assignment targets. Read-only reproduction: patch Path.read_text to append these lines to kits/q/b/o.py, then call scan_decoded(kit): `key, value = ("BeNcHmArK", "q")` / `os.environ[key] = value`. Result: PASS, 76,251 checked strings, identical to baseline. The variant is absent from naming_test21d.py." The review otherwise verified build 21e's resolver fixes.

## Do
1. Make the environment check sound rather than patching one pattern: any environment write or passed environment map in kit Python or shell whose key or value cannot be resolved to a literal by the scanner (tuple/starred unpacking, loops, function returns, f-strings, getattr/setdefault/putenv, subprocess env built anywhere, shell indirection) REFUSES, unless the key is in an explicit allowlist of literal names. Keep all 21d controls.
2. Tests: the reviewer's tuple variant (old PASS, new refuse), plus os.putenv, os.environ.setdefault, a for-loop over pairs, an f-string key, and a dict built by a helper function then passed as env=; all refuse by name or as unresolvable.
3. Run the new scanner on the final kit q. Kit q bytes MUST stay byte-identical (seal 5d300f19 before and after); if the new scanner refuses the real kit, do not change the kit: write the exact finding first in the report and stop.
4. Rerun naming21c/21d tests and focused.py; package `out/tree_rebuild_b21f_<seal8>.tar`; `out/BUILD21F_REPORT.md` under 60 lines.

## Rules (restating build 21's)
No ssh, network, Orchard, GPU, Git, tmux, scheduler or other agents; never list, search or grep on /home or /data*; write only under L; no deletion (move to `L/attic/`); every CPU process under `nice -n 10` with at most 8 threads; no process above 20 GB RAM. Do not change the sealed tree or kit q; GO stays false.
