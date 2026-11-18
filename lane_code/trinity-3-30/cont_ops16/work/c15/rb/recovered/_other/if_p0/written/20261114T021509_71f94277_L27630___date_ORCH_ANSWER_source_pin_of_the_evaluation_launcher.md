<!-- recovered by seal_plan: transcript=71f94277 line=27630 utc=2026-11-14T02:15:09.070Z kind=written original_path=/scratch/jjyeung/orch_cd/if_p0/inbox/$(date_ORCH_ANSWER_source_pin_of_the_evaluation_launcher.md heredoc_quoted -->
# ORCH answer to QUESTION 0214Z: yes, keep the original launcher hash as provenance; verify only what you borrowed

The evaluation lane's `orchard_launcher.py` changed by one line at 01:40Z with my approval (the admitted step set; receipt `/scratch/jjyeung/orch_cd/leg_s1_review/ORCHARD_LAUNCHER_RECEIPT_STEP_SET.json`, new seven-file digest b13c6dcc; the previous accepted digest was 50deb489, in which the launcher hashed 349b17fe...). You copied nothing from that file.

Ruling:
- Record `349b17fe...` as the launcher of the accepted baseline you reused (provenance text only), with the receipt above naming its successor.
- The final verifier checks the code you actually borrowed against its own pins (the files and definitions you copied, which still match) and does not fail on another lane's working file that you do not copy from. A sealed kit must not depend on a file that another lane may legitimately change.
- No immutable copy of the old launcher is needed.

Finish the delivery. The GPU-name confirmation is noted.