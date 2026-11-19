The H remainder kit builds fresh packages for steps 200, 400 and 544; H@544 selects 118 rotation + 300 direction items after 482 completed rows.
The subset preserves item order, answers, captures and IDs; the full frozen twin/task files remain sealed.
The remainder uses the generic manifest name heldout_camera_remainder; evaluator, serving code, settings and tower/memo pins remain unchanged.
COUNTS=(0,118,300,0,0) and SCHEDULE=((0,1),(0,2)); REMAINING_IDS.json lists IDs per type, and other partials derive their own schedule.
H@544 walltime is 04:00:00. Observed means are 25.6838 s/displacement and 24.6600 s/rotation; unseen direction uses the larger mean.
The 25% work margin plus 1,800 s startup and 1,800 s stop reserves requires 16,869 s (04:41:09), exceeding the cap by 2,469 s.
BUILD.json records budget_fits=false; the capped allocation may publish another partial. H@200 sizes itself from its authenticated partial.
make_items_remainder_h.py writes the subset and grouped *_IDS.json; build_remainder_h.py reauthenticates that selection and reseals token, plan, operator, payload and batch.
return_tools_h.py authenticates EXIT/receipt, archive bytes, token/job, package, inputs, export, settings, journals and completed counts.
place_fill_hrem.py checks the parent marker, sizes, individual/concatenated hashes and retained fstat identities before hardlinking; failures stop without copying or pulling.
bind_H200.json/bind_H544.json retain H pins; bind_H400.json uses the reviewed D400 export and requires the H parent's exact binding to match.
o_build_hrem.sh embeds the complete kit; the other streamed scripts use STAGE-kit. No deployment transfer is required.
o_sub_hrem.sh retains the H CPU/entry/memory receipts, empty-general check and pool guards; only the count/schedule assertion uses the sealed remainder plan.
o_fetch_hrem.sh authenticates and saves the remainder to PACKAGE/a/f, then writes STAGE/SCORE_SPEC.json and STAGE/SCORES.json using the retained parent publication.
score_h_merge.py requires exact complementary coverage and matching export/settings/serving identity; it reports H cells and room bootstrap differences (seed 17, 10,000 draws).
For comparisons, --other OTHER_SPEC.json accepts either {parent: SEGMENT, remainder: SEGMENT} or one complete SEGMENT; each SEGMENT names package, archive, exit and receipt.
Tests passed: real H544 selection; synthetic 482+418 merge with 900 rows/450 pairs; token/plan/subset/duplicate/export/truncation refusals; link failures and mutation races.
Additional tests passed: 418 real metadata mappings equal the parent's mappings, stub operator rehearsal, synthetic 200/400 builds and complete step comparisons, 15 CPU receipt mutations and pool guards.
TEST_RESULTS.json, STEP_TEST_RESULTS.json, RUNTIME_TEST_RESULTS.json, GUARD_TEST_RESULTS.json and SYNTAX_TEST_RESULTS.json identify evidence; all root Python files compile under 3.6.8 and all shell scripts pass bash -n.
No real 200/400 partial, 21.6 GB fill, Orchard CPU allocation, model inference, transport or job submission was tested. No SSH/network/Git/GPU/deletion/submission ran.
Run these commands from this kit on Trinity, with the existing ossh.sh available; execute submission only after its new CPU job succeeds, and fetch only after publication.
```bash
/usr/bin/python3 configure_hrem.py --parent /project/community/jjyeung/okh7/a15_cot_apdc863c3e6b41d --stage 813f42db/c21h544r --step 544 --out run544
timeout 300 bash ossh.sh 'bash -s' < run544/o_build_hrem.sh
timeout 300 bash ossh.sh 'bash -s' < run544/o_place_fill_hrem.sh
timeout 300 bash ossh.sh 'bash -s' < run544/o_cpu_hrem.sh
# After the remainder CPU job succeeds:
timeout 300 bash ossh.sh 'bash -s' < run544/o_sub_hrem.sh
# After the remainder publishes:
timeout 300 bash ossh.sh 'bash -s' < run544/o_fetch_hrem.sh
# Set H200_PARENT to job 173259's full package path; that token is absent from the supplied evidence.
/usr/bin/python3 configure_hrem.py --parent "${H200_PARENT:?Set job 173259 package path}" --stage 813f42db/c21h200r --step 200 --out run200
timeout 300 bash ossh.sh 'bash -s' < run200/o_build_hrem.sh
timeout 300 bash ossh.sh 'bash -s' < run200/o_place_fill_hrem.sh
timeout 300 bash ossh.sh 'bash -s' < run200/o_cpu_hrem.sh
# After the remainder CPU job succeeds:
timeout 300 bash ossh.sh 'bash -s' < run200/o_sub_hrem.sh
# After the remainder publishes:
timeout 300 bash ossh.sh 'bash -s' < run200/o_fetch_hrem.sh
```
