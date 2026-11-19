S='/scratch/jjyeung/orch_n30/fb_pack2/STATUS.md'; t=open(S).read()
t=t.replace('| fbp_relrev2 RUNNING (next boundary) |','| fbp_relrev2 GO 21:25Z (rows 69e85b7c; next boundary; split validation by room) |')
t=t.replace('- Cursor fbp_relrev2 (1-18 F1/relrev2, 21:16Z): confirm review of relcnt2 (next boundary).\n','')
t=t.replace('## Delivered','''- ORDER 2122Z (1-18 disk 101 GB): nothing above 200 MB on 1-18; new builds/reviews on 2-28 (copy only needed inputs); read free space before any write >200 MB; BLOCKER if 1-18 < 80 GB; keep REMOVAL_CANDIDATES.md current (session folder + events copy).
- ANSWER 2126Z (donor): M1-M3 required (M1 most: nonzero conditioning path + negative control must fail); S1 freeze-time lever only if no admission change and byte-identity passes first try, else document (first boundary re-prepares anyway); must hold: a leg that has the donor resumes under it (check in donor2rev). Patch C: needs N's REAL exposure counts per prose form per step before binding (QUESTION 2132Z default: tree_rebuild15's Orchard mode-r CPU job composes with patch C). Manifest: say per item whether it changes preparation (stores, row plan) or only the model side.

## Delivered''',1)
open(S,'w').write(t)
