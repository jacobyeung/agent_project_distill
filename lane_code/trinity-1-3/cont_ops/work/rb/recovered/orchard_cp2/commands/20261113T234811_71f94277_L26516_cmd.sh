<!-- recovered by seal_plan: transcript=71f94277 line=26516 utc=2026-11-13T23:48:11.862Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); C=/scratch/jjyeung/orch_cd; cat > $C/if_p0/inbox/${N}_ORCH_ANSWER_overlay_path_and_interpreter_links.md <<'EOF'
# ORCH answer to QUESTION 2346Z

Your default is right: keep the production interpreter, keep building, refuse a real submission while an identity is unresolved.

**1. NumPy/SciPy overlay.** It is not on the project filesystem as a separate object; it travels inside the pushed production kit under Orchard `/home`. The operator's staging script for an earlier kit reads it at `$KH/k/np226_5204b3a0.tar` with `KH=/home/jjyeung/okit/x/<kit id>` (`/scratch/jjyeung/orch_cd/orchard_cp2/work/adm/stage5.sh`, lines 1-3, kit 9ca55db0). For the running production kit the expected path is `/home/jjyeung/okit/x/07ca49df/k/np226_5204b3a0.tar`. I have asked the operator to confirm that exact path from its records. Build the job to take the path as one pinned input, verify sha256 74b2d460... and the 202,598,400 bytes before extraction, and refuse otherwise. Reading it there is fine; writing anything under `/home` except the bounded result archive is not.

**2. Interpreter links in `venv_rwtrain_torch211_cu129.tar`.** I know of no header receipt. Evidence about the interpreter: node tracebacks from this environment show `/usr/lib/python3.12/subprocess.py`, and the host's `/usr/bin/python3` is 3.12.3, so the environment's interpreter is a link to the system Python. Do not allow arbitrary absolute links. Allow exactly this closed set and nothing else:
- members `venvs/rwtrain_torch211_cu129/bin/python`, `.../bin/python3`, `.../bin/python3.12` (adjust the leading components to the archive's real root once known);
- targets `/usr/bin/python3` or `/usr/bin/python3.12` for an absolute link, and `python`, `python3` or `python3.12` for a relative one.
Any other absolute link refuses and names the member and its target in the failure record, as the accepted extractor does. If the real archive has a pair outside this set, the first job stops in staging within minutes and tells us the exact pair; that costs one short job, not a wrong run. If the operator holds a header listing, I will forward it.

Keep going with the job and the as-in-job fixture run.
EOF
cat > $C/orchard_cp2/inbox/${N}_ORCH_REQUEST_low_priority_two_path_facts_for_if_p0.md <<'EOF'
# ORCH request (low priority; after the cheap run, from records you already hold, no new session for this alone)

Lane if_p0 is building a one-GPU `general` job that stages the production interpreter itself. Two facts, each one line in an event:

1. The exact Orchard path of the NumPy/SciPy overlay of the running kit (sha256 74b2d460..., 202,598,400 bytes). Expected `/home/jjyeung/okit/x/07ca49df/k/np226_5204b3a0.tar`; confirm or correct, and say whether `okit/x` is a link into the project filesystem.
2. Whether you hold any header listing of `/project/community/jjyeung/cp4tk_rt/kit/venv_rwtrain_torch211_cu129.tar` that shows its symbolic links (member and target), in particular the interpreter links under `bin/`. If you hold none, say so; do not read the archive for this.

If a routine session of yours can answer item 1 with one extra `ls -l` line, batch it there.
EOF
T=$(date -u +%Y-%m-%dT%H:%M:%SZ); echo "$T orch-home-distill-79: if_p0 QUESTION 2346Z (where the NumPy/SciPy overlay sits on Orchard; interpreter links in the production venv archive) ANSWERED ($N): overlay travels in the pushed kit, expected /home/jjyeung/okit/x/07ca49df/k/np226_5204b3a0.tar (pattern from orchard_cp2/work/adm/stage5.sh), pinned and hash-checked; venv links limited to a closed set (bin/python, python3, python3.12 -> /usr/bin/python3 or /usr/bin/python3.12, or relative aliases), anything else refuses naming the pair. Low-priority REQUEST to orchard_cp2 ($N) to confirm both from its records after the cheap run. Re-armed evwait (b9dw6bebj)." >> $C/ORCH_HANDOFF.md; echo $N