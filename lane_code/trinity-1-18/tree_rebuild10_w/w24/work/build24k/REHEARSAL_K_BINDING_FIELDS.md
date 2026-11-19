Production: LAUNCH BLOCKER; native localized donor refuses P_EXPORT_RUN_BINDING_MISMATCH.
The native temporary-path gate also refuses the original p_run pins; a tree change is required.
The JSON evidence records every full pin, authenticated local filename, and code hash.

Production:

| Field | Donor bytes | Localized comparison value | Equal |
| --- | --- | --- | --- |
| source.preparation.path | /scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/runs/6ed2c7aa/inputs/prepare_da5580b7d92f490bb3cfe8df447e7820/prepared/s1_receipt.json | /tmp/q_22c714e1/p/q/u/a5bbef1b865fd98aa398ded3e31ab60ed40848917646299ffc0ccc15c283ccda | False |
| source.preparation.sha256 | a5bbef1b865fd98aa398ded3e31ab60ed40848917646299ffc0ccc15c283ccda | a5bbef1b865fd98aa398ded3e31ab60ed40848917646299ffc0ccc15c283ccda | True |
| binding.preparation.path | /scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/runs/6ed2c7aa/inputs/prepare_da5580b7d92f490bb3cfe8df447e7820/prepared/s1_receipt.json | /tmp/q_22c714e1/p/q/u/a5bbef1b865fd98aa398ded3e31ab60ed40848917646299ffc0ccc15c283ccda | False |
| binding.preparation.sha256 | a5bbef1b865fd98aa398ded3e31ab60ed40848917646299ffc0ccc15c283ccda | a5bbef1b865fd98aa398ded3e31ab60ed40848917646299ffc0ccc15c283ccda | True |
| binding.config_sha256 | 9459724f1b925b7d750628ccb36d7a29f871e953751c0e1d2c9abaea67d567e4 | 9459724f1b925b7d750628ccb36d7a29f871e953751c0e1d2c9abaea67d567e4 | True |
| preparation.config_sha256 | 9459724f1b925b7d750628ccb36d7a29f871e953751c0e1d2c9abaea67d567e4 | 9459724f1b925b7d750628ccb36d7a29f871e953751c0e1d2c9abaea67d567e4 | True |
| preparation.schema | c1-preparation-v1 | c1-preparation-v1 | True |

Unlocalized binding: all seven field comparisons pass.
Native refusal: `P_EXPORT_RUN_BINDING_MISMATCH`.
Preserving p_run unchanged: `R1_HOST_PATH_OUTSIDE_JOB_TMP`.

Fixture:

| Field | Donor bytes | Localized comparison value | Equal |
| --- | --- | --- | --- |
| source.preparation.path | /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24f/rehearsal3/donor/preparation.json | /tmp/q_22c714e1/p2/q/u/e2cd4d01bfee2f918641002845ea8d7cc548e4b0e8d9f6060773497d571d6677 | False |
| source.preparation.sha256 | e2cd4d01bfee2f918641002845ea8d7cc548e4b0e8d9f6060773497d571d6677 | e2cd4d01bfee2f918641002845ea8d7cc548e4b0e8d9f6060773497d571d6677 | True |
| binding.preparation.path | /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24f/rehearsal3/donor/preparation.json | /tmp/q_22c714e1/p2/q/u/e2cd4d01bfee2f918641002845ea8d7cc548e4b0e8d9f6060773497d571d6677 | False |
| binding.preparation.sha256 | e2cd4d01bfee2f918641002845ea8d7cc548e4b0e8d9f6060773497d571d6677 | e2cd4d01bfee2f918641002845ea8d7cc548e4b0e8d9f6060773497d571d6677 | True |
| binding.config_sha256 | 48b37d82ac0e8ae308baa04fdff357bf0539be4f6155ddc0f8c39a16c7773111 | 48b37d82ac0e8ae308baa04fdff357bf0539be4f6155ddc0f8c39a16c7773111 | True |
| preparation.config_sha256 | 48b37d82ac0e8ae308baa04fdff357bf0539be4f6155ddc0f8c39a16c7773111 | 48b37d82ac0e8ae308baa04fdff357bf0539be4f6155ddc0f8c39a16c7773111 | True |
| preparation.schema | c1-preparation-v1 | c1-preparation-v1 | True |

Unlocalized binding: all seven field comparisons pass.
Native refusal: `P_EXPORT_RUN_BINDING_MISMATCH`.
Preserving p_run unchanged: `R1_HOST_PATH_OUTSIDE_JOB_TMP`.
