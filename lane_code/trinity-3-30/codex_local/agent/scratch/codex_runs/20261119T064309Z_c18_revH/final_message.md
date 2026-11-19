**GO AFTER FIXES — steps 200 and 544.**

- **Fix before GPU — diff exceeds the allowlist.** [build_h.py:87](/scratch/jjyeung/orch_n30/cont_ops18/hcam/build_h.py:87) adds `h1eval/heldout_h.py` and modifies `h1eval/items.py` and `h1eval/h10/parity_adapter.py`. These are additional evaluator changes beyond `scorers.py`. Keep these admission checks in builder/tests, restore the three payload files to the allowed scope, then reseal and revalidate.

- **Note — test receipt provenance differs.** [SCRIPT_RESULTS.json:5](/scratch/jjyeung/orch_n30/cont_ops18/hcam/evidence/SCRIPT_RESULTS.json:5) names E’s receipt writer; [test_scripts_h.py:144](/scratch/jjyeung/orch_n30/cont_ops18/hcam/test_scripts_h.py:144) emits H’s. Regenerate this receipt so the evidence matches the supplied test.

- **Note — package and item checks pass.** [review_h.py:33](/scratch/jjyeung/orch_n30/cont_ops18/hcam/review_h.py:33) reconstructs both deliveries under Python 3.6.8; all 71 indexed hashes pass. Originals match A4, twins preserve frame/label fields, and all 900 question/frame pairs agree. I independently reproduced **636-item / 3,816-case placement parity**.

- **Note — serving and bindings pass.** [review_h.py:45](/scratch/jjyeung/orch_n30/cont_ops18/hcam/review_h.py:45) verifies unchanged reader/tree/rows/auth payloads and step-200 binding. H544’s binding bytes equal D544’s, including `469ddece_mstop.tar` / `3ed73aea…`.

- **Note — submission guards pass.** [o_sub_H.sh:16](/scratch/jjyeung/orch_n30/cont_ops18/hcam/o_sub_H.sh:16) retains E’s applicable guards. D’s omitted checks concern its object-distance full-reader test.

- **Note — scoring checks pass.** [score_h.py:148](/scratch/jjyeung/orch_n30/cont_ops18/hcam/score_h.py:148) implements call rate, patched answer accuracy, paired wording differences and step comparisons correctly. Its synthetic suite passed entirely in memory, including identity mutations and malformed journals. Orchard entrypoints parse under Python 3.6.8.

No files changed. No SSH, network, Git or GPU used. Orchard CPU admission remains required before GPU submission.