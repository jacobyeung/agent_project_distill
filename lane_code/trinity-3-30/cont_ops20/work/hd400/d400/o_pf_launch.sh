set -euo pipefail; S=/project/community/jjyeung/okh7/813f42db/c20d400; ls $S | head -40
cat > $S/o_pf.sh <<'SHEOF'
#!/bin/bash
# Run on Orchard login after o_build_D.sh. This script places and fills; it never submits.
set -euo pipefail
umask 077
: "${STAGE:?Set STAGE to the directory containing BUILD.json}"
# Optional: REUSE_PARTS_FROM holds verified parts 0,1,2,3; PREP_FROM holds 7,8,9.
# Optional: DONE_FROM is a three-field receipt; CLAIM_FROM contains the member name.
exec /usr/bin/python3 -B "$STAGE/place_fill_d.py" "$STAGE"
SHEOF
cd $S && STAGE=$S REUSE_PARTS_FROM=/project/community/jjyeung/okh7/a15_cot_apdc76460c3a164/a/e DONE_FROM=/project/community/jjyeung/okh7/x_ee227714/o/gcs_6ed2c7aa_m400.done nohup bash $S/o_pf.sh > $S/pf.log 2>&1 < /dev/null & echo started $!
