set -euo pipefail; S=/project/community/jjyeung/okh7/813f42db/c20h400; ls $S | head -30
cat > $S/o_pf.sh <<'SHEOF'
#!/bin/bash
# Orchard login only. The build binding selects the existing export parts.
set -euo pipefail
umask 077
: "${STAGE:?Set STAGE to the directory containing BUILD.json}"
STEP=$(/usr/bin/python3 -B -c 'import json,sys;print(json.load(open(sys.argv[1]))["H"]["export_binding"]["step"])' "$STAGE/BUILD.json")
case "$STEP" in
200) : "${REUSE_PARTS_FROM:=/project/community/jjyeung/okh7/a15_cot_apd72cdcff1e22a/a/e}" ;;
400) : "${REUSE_PARTS_FROM:=/project/community/jjyeung/okh7/a15_cot_apdc76460c3a164/a/e}" ;;
544) : "${REUSE_PARTS_FROM:=/project/community/jjyeung/okh7/a15_cot_apd00c03dcc685e/a/e}"
     : "${DONE_FROM:=/project/community/jjyeung/okh7/x_07ca49df/o/gcs_469ddece_m544.done}"
     export DONE_FROM ;;
*) exit 1 ;;
esac
export REUSE_PARTS_FROM
exec /usr/bin/python3 -B "$STAGE/place_fill_h.py" "$STAGE"
SHEOF
cd $S && STAGE=$S REUSE_PARTS_FROM=/project/community/jjyeung/okh7/a15_cot_apdc76460c3a164/a/e DONE_FROM=/project/community/jjyeung/okh7/x_ee227714/o/gcs_6ed2c7aa_m400.done nohup bash $S/o_pf.sh > $S/pf.log 2>&1 < /dev/null & echo started $!
