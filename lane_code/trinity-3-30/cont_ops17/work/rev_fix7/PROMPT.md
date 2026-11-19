# Read-only review: fix 7 (admit continuation run 6ed2c7aa at milestones 400/600) for three read kits

You review; you do not edit, ssh, submit or delete. Work only under /scratch/jjyeung/orch_n30/cont_ops16/work/c15 and /scratch/jjyeung/orch_n30/cont_ops17/work/rev_fix7. No recursive search outside those trees; no Git.

Context: three reviewed read kits (h1read = fix 6 direct read main+a7; h1face = F1 facing away+forward; h1vsti = r6 VSTI relative read) admit R1 run 673bc60f (deployment x_69d2930d, milestones 100/200) and a planned continuation 05b8ac69 (x_7f1589c1, 400/600). The real continuation is run 6ed2c7aa (Orchard job 172660, kit okh7/x_ee227714, same exporter c.sh: object q8/8865619b/<run>_m<step>.tar, receipt <HM>/o/gcs_<run>_m<step>.done, HM = the deployment root). The orchestrator admitted 6ed2c7aa for step-400 and step-600 boundary reads. Forks h1read7, h1face7, h1vsti7 (code copied, data dirs hardlinked) add only:
- binding.py: RUNS['6ed2c7aa']='x_ee227714'; R1_RANGES['6ed2c7aa']=(201,600); milestones (400,600) for 05b8ac69 and 6ed2c7aa.
- h1vsti7 orchard_launcher.py family_gate: r6 identities add ('6ed2c7aa',400,'m400') and ('6ed2c7aa',600,'m600').
- tests/test_fix7.py (5 tests, pass in all three forks).
Diffs: rev_fix7/*_launcher.diff, *_tests.diff. Prepared step-400 packages: h1read7/kit/build/ab68c580d38, h1face7/kit/build/a83291f763a, h1vsti7/kit/build/a6979d0babe; their CONFIG.json differences from the reviewed step-200 packages (h1read/kit/build/a8102c3207b, h1face/kit/build/a2e46c0504e, h1vsti/kit/build/a35f73e87f0) are in rev_fix7/config_*.diff.txt. Pre-existing test_fix6 failures (3 of 7, missing historical fixtures) are identical in h1read and h1read7.

Answer, with file:line evidence:
1. Does any path (prepare, embedded request validation in the batch, export staging, artifact lineage, family gates, receipt/claim parsing, return fetch/unpack, item selection) still reject or mis-handle 6ed2c7aa at step 400 or 600, or treat it differently from 673bc60f at 200 in a way that breaks pairing with the step-200 and step-544 reads (same reader payload, items, decoding, selector, serving pins)?
2. Does the change admit anything beyond 6ed2c7aa m400/m600 (other steps, stop generations mstop* within 201-600, other namespaces) that matters? State whether stop generations for 6ed2c7aa are admitted and whether that is a risk.
3. Are the three package configs' differences limited to token-derived paths, binding.py pins and review pins, payload sha, plan sha, and the export binding/artifact path? Is the model key name cp1m200 (unchanged) used anywhere that would mislabel the step-400 read?
4. Anything that would make the job fail at runtime that these CPU-side checks cannot see.
Verdict line: GO, GO AFTER FIXES (list), or NO-GO. Keep under 60 lines.
