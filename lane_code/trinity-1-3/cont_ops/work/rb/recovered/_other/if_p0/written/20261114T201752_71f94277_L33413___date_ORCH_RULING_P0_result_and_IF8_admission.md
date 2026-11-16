<!-- recovered by seal_plan: transcript=71f94277 line=33413 utc=2026-11-14T20:17:52.140Z kind=written original_path=/scratch/jjyeung/orch_cd/if_p0/inbox/$(date_ORCH_RULING_P0_result_and_IF8_admission.md heredoc_quoted -->
# ORCH ruling: P0's result stands at 18.11 degrees; prepare IF8; resolve the validator question without touching a science file

## The result

P0 (job 169530, 300 steps, 9,600 rows): primary direction statistic 18.107 degrees, 90% clip-bootstrap interval [16.77, 19.62], recorded and locally recomputed values equal. It is above the registered 12-degree stop threshold, so the experiment continues: IF8 is the next arm and must reach 13.1 degrees or lower (5 degrees better) on the same read. I accept this number for the gate. The three secondary fields that differ by at most 1.8e-14 between your CPU replay and the run are floating-point noise between runtimes; they do not enter any gate.

## The validator

The job's private /tmp no longer exists (it is removed when a job ends), and I will not spend an Orchard job on a replay. Answer these two from the code and the return, then act:

1. Does the P0 job itself call the unchanged `orchard_eval.verify_completed` in the producing runtime before it writes its COMPLETE record (file and line, and the record in the return that shows it passed)? If yes, that is the producing-runtime replay you asked for; cite it and close the question.
2. Where does IF8's admission of the P0 result call that validator: locally when the packet is built, inside the IF8 job, or both?

Rule: no tolerance goes into the sealed validator or any other of the 207 science files, so the predecessor-seal table stays byte-identical. If only the local packet build is blocked, change the launcher side only (plumbing): the local admission still runs the validator; a failure is admitted locally if and only if every differing field is one of the secondary float metrics, each differs by at most 1e-9 in absolute value, and the primary statistic, the gate inputs, all counts, row indices and hashes are exactly equal; the differences are recorded in the packet; and the IF8 job's own exact check in the production runtime stays the authority and refuses on any mismatch. If the in-job check in IF8 would compare against values computed on another device than P0's job did, say so before building anything.

## IF8

Build the IF8 packet for `general` (the slot is free now) and for `advanced`, at the current seal if the launcher-side change is not needed, otherwise at a new seal whose runtime diff I read (plumbing only; science table identical). Send one RESULT with: the answers to 1 and 2, the diff if any, the packet tokens, the cross-seal admission record that binds P0's return (archive sha a4877d7c...), the projected hours (P0 took 3 h 08 min), and the IF8 control file form you need from me (review, confirmation, launch note for arm IF8). Submission waits for my order through evalx.