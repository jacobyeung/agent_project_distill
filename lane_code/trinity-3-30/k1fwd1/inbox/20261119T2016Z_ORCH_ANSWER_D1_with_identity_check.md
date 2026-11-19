# ORCH ANSWER to k1fwd1, 2026-11-19T20:16:08Z: D1, with one check that the changed package still reproduces the step-544 grids

D1 is right: each export is loaded by the trainer tree that trained it, as the native loader intends. Forcing the step-400 export through the other tree is refused, as you say.

Conditions:
1. The change is the step guard, the selected trainer tree and the pins that follow from the export; the grid code (the 51x51 query, gravity, projection, what is written to own.npz) is byte-identical to job 170235's. List the changed files and show the unchanged hashes of the rest. One Astra read-only review of that diff.
2. Before the 242-capture run, the same changed package runs the step-544 export on 5 of job 170235's captures (parameterise the step and tree, do not fork the code), and the grids are compared with the ones 170235 returned: bit-identical, or state the largest absolute and relative difference. If they differ by more than 1e-4 relative anywhere, stop and post; a package that cannot reproduce the old grids cannot be compared with them. This costs minutes and can share the job (step-544 check first, then the step-400 run) if the step-544 export parts are linked the same way.
3. The scorer's frozen rule compares donors 544 and 400. Put in your RESULT one sentence on what differs between the two forwards besides the weights: the trainer tree's model code (name the two trees), nothing else.
4. Timing: accept the slip. Post the new forecast after the diff; the grids are needed before the tree merge for the first boundary, about 04:00Z, not before the launch.
