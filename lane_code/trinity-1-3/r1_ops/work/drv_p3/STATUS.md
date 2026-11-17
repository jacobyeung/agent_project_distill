BUILT / LOCAL READY: S2-on proof-2 drivers (r1_drv4).

Config: 8246a4dd34bcfb7de1770b62ae7f0f331849714397d66fe68dfda8f8aa676573.
Archive: p_082d2d90.tar; SHA256 3401c318e552cf0ba23f691d197b8f022550639693632abeeaa3bf3b08658384.
Bundle: /project/community/jjyeung/okh7/i_082d2d90.
Kit: /project/community/jjyeung/okh7/x_082d2d90.
Run/job: 07297df8 / a15_cot_ap07297df8.
Source: okh7/x_3fdda0fb; manifest 661ccd85b7a8f1afd25297869dc3a28539e64a3a0ab9a74ee928c0c5ab8a66c3.
Switches: S2=true, S1=false, and both max_own_probability=0.

The local fixture tests_p3_k1ku4soo/derived_ready reached READY after regenerating all 747 unit rows. The test preserves the exact selection hash and staging pins. Two missing H1 fixture members use labeled sentinels; this does not attest production data or RGB.

Validation passed: all 48 frozen-manifest entries and all 35 archive members; 108 switch cases across the sealed deriver, binder/sealer, and embedded proof; five-review-chain acceptance and 16 refusals; certificate/session builders and refusal cases; both partition bindings; queue and duplicate-submit guards; metadata-only evidence refusals; scan inventory; shell and Python syntax (20 top-level drivers and all 130 shell files in the work directory). The *_p3.txt files hold these results.

Review status: PENDING, missing events/review_r1p5/REVIEW_VERDICT_R1P5.md. The four antecedents are review_r1p, review_r1p2, review_r1p3, and review_r1p4. The final verdict must name this full archive SHA or config identity and state GO, or GO AFTER FIXES with only explicit LOW fixes. Expected review time is November 17 at about 12:50 p.m. PT.

rv1.sh, sc1.sh, and si1.sh are inert pending placeholders. The operator still needs the final review, an independent ANON_OK plus classified scan under ORCH 1758Z exemptions, fresh sess_07297df8.json, and the Orchard CPU proof. Production GO remains false. README.md lists the exact command order and expected outputs; DRIVER_SHA256SUMS.txt authenticates the handoff before builders replace the placeholders.

New test scratch: 159,887,312 logical bytes (159.89 MB); 86,749,184 newly allocated bytes. Both are below 300 MB. One READY kit is retained; immutable input aliases are hardlinks, and negative kit copies contain metadata only. storage_results_p3.json records the accounting. The bulk fixture refuses a rerun while its outputs exist.

All writes stayed in drv_p3. No SSH, Orchard, Git, GPU, deletion, real session mint, or production authorization ran. The copied production-submit helper is an inert refusal script. No independent launch review is claimed by this build.
