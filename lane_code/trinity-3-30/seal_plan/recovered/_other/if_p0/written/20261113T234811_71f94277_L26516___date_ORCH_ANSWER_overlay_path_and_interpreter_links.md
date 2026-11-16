<!-- recovered by seal_plan: transcript=71f94277 line=26516 utc=2026-11-13T23:48:11.862Z kind=written original_path=/scratch/jjyeung/orch_cd/if_p0/inbox/$(date_ORCH_ANSWER_overlay_path_and_interpreter_links.md heredoc_quoted -->
# ORCH answer to QUESTION 2346Z

Your default is right: keep the production interpreter, keep building, refuse a real submission while an identity is unresolved.

**1. NumPy/SciPy overlay.** It is not on the project filesystem as a separate object; it travels inside the pushed production kit under Orchard `/home`. The operator's staging script for an earlier kit reads it at `$KH/k/np226_5204b3a0.tar` with `KH=/home/jjyeung/okit/x/<kit id>` (`/scratch/jjyeung/orch_cd/orchard_cp2/work/adm/stage5.sh`, lines 1-3, kit 9ca55db0). For the running production kit the expected path is `/home/jjyeung/okit/x/07ca49df/k/np226_5204b3a0.tar`. I have asked the operator to confirm that exact path from its records. Build the job to take the path as one pinned input, verify sha256 74b2d460... and the 202,598,400 bytes before extraction, and refuse otherwise. Reading it there is fine; writing anything under `/home` except the bounded result archive is not.

**2. Interpreter links in `venv_rwtrain_torch211_cu129.tar`.** I know of no header receipt. Evidence about the interpreter: node tracebacks from this environment show `/usr/lib/python3.12/subprocess.py`, and the host's `/usr/bin/python3` is 3.12.3, so the environment's interpreter is a link to the system Python. Do not allow arbitrary absolute links. Allow exactly this closed set and nothing else:
- members `venvs/rwtrain_torch211_cu129/bin/python`, `.../bin/python3`, `.../bin/python3.12` (adjust the leading components to the archive's real root once known);
- targets `/usr/bin/python3` or `/usr/bin/python3.12` for an absolute link, and `python`, `python3` or `python3.12` for a relative one.
Any other absolute link refuses and names the member and its target in the failure record, as the accepted extractor does. If the real archive has a pair outside this set, the first job stops in staging within minutes and tells us the exact pair; that costs one short job, not a wrong run. If the operator holds a header listing, I will forward it.

Keep going with the job and the as-in-job fixture run.