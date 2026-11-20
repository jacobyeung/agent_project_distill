# Round 4 of K1-X (rank 2): fix the GT-depth coverage defect, re-read C1 two ways, then the BOX follow-up

Continue in `/scratch/jjyeung/orch_n30/lever1_c/r2/` (rules of BRIEF_R2.md, BRIEF_R2B.md, BRIEF_R2C.md in `/scratch/jjyeung/orch_n30/lever1_c/` hold; reads of this node's local /scratch are approved at any volume; do not stop to ask about them). Write round-4 outputs to `r2/out4/` and the BOX follow-up to `r2/out_box/`; leave `r2/out/` untouched. CPU only, nice 10, at most 16 processes.

## Part 1: the defect (independent review, file `/scratch/jjyeung/orch_n30/lever1_c/r2rev_findings.md`)
The review found: 17 new held-out ARKit refusals under GT depth + deployed masks all select a GT frame whose depth is 0 everywhere (missing sensor frame; valid=True, inst=-1). The lift marks a mask visible before checking positive depth (vendor/ladder_pricing.py:10) and the session pins the largest visible mask (box_v313.py:529), so the frame produces `box unavailable` / `not seen`. Partial holes are bilinearly mixed with zeros in `sample_gt` (k1x.py:187).
Fix, in GT-depth cells only (served-depth cells unchanged, so parity still holds):
- a frame whose GT depth is missing (all zero) is not depth-eligible: the mask on it carries no depth, so the lift and the visible-mask pin use the other frames (pose validity of that frame is unchanged: do not route this through `geo.has()` if it breaks pose transforms);
- partial holes: exclude zero-depth raster pixels from sampling (mask them, do not interpolate zeros into positive depths);
- regression tests: whole-frame-missing and partial-hole cases; parity of served cells unchanged per row.
Then re-run the factorial and report C1, C3 (depth alone, pose alone, joint) and the GT-depth rows twice: (A) full population (refusals count as unanswered, as registered) and (B) identical valid support: rows whose selected frames have GT depth in both arms of the contrast, with coverage counts. Verdicts against the registered bars for both A and B; if A and B fall on different sides of a bar, say so and do not pick. ARKit vs ScanNet/ScanNet++ for every contrast.

## Part 2: BOX follow-up
Run `/scratch/jjyeung/orch_n30/lever1_c/BRIEF_R2D.md` exactly as written (registered reading there; it was registered in the plan record before any number).

Deliver `out4/K1X4.json`, `out4/REPORT_R2_4.md` (max 60 lines), `out_box/` per BRIEF_R2D, SHA256SUMS in each, tests passing. Final message: Part 1 table (A and B), verdicts, Part 2 table and verdict, files, deviations.
