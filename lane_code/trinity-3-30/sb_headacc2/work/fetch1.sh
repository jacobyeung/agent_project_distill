set -u
R=/scratch/jjyeung/orch_n30; M=/scratch/jjyeung/n30_mirror
echo "@@@ host"; hostname -s; date -u +%FT%TZ
cd $R/sb_harev || exit 1
echo "@@@ ls_harev"; ls -la . out inputs 2>&1 | head -90
echo "@@@ sha_inputs"; sha256sum inputs/*.md out/REVIEW_VERDICT.md out/RECOMPUTE.json out/recompute.py 2>&1; wc -c out/* 2>&1 | tail -8
echo "@@@ RECOMPUTE.json"; head -c 400000 out/RECOMPUTE.json; echo
echo "@@@ recompute.py"; head -c 120000 out/recompute.py; echo
echo "@@@ verdict"; cat out/REVIEW_VERDICT.md
echo "@@@ snap_obj"; cat -n inputs/KIT_SPEC_object_route_r0dev.md 2>&1 | head -c 20000
for L in sb_kbox sb_ktow sb_kobj; do
  echo "@@@ lane_$L"; ls -la $R/$L $R/$L/out $R/$L/work 2>&1 | head -70
  for f in STATUS.md REPORT.md out/REPORT.md out/STATUS.md out/DRYRUN.json out/BLOCKER_track.md; do
    [ -f $R/$L/$f ] && { echo "--- $L/$f"; head -c 14000 $R/$L/$f; echo; }
  done
done
echo "@@@ corrected_labels"; K=$M/gt_audit/gt_audit/work/k1audit; ls -la $M/gt_audit $M/gt_audit/gt_audit 2>&1 | head -30; ls -la $K 2>&1 | head -40
sha256sum $K/K1_LABELS_CORRECTED.jsonl 2>&1; wc -l $K/K1_LABELS_CORRECTED.jsonl 2>&1; head -c 1200 $K/K1_LABELS_CORRECTED.jsonl 2>&1; echo
echo "@@@ agg"; H=$R/b04host3/lift_price/harness; ls -la $H 2>&1 | head -50; echo "--- AGG_TRAIN.txt"; head -c 2500 $H/AGG_TRAIN.txt; echo "--- AGG_TRAIN_v2.txt"; head -c 2500 $H/AGG_TRAIN_v2.txt
echo "@@@ mirror_ev"; ls -la $M/sb_headacc/ 2>&1; sha256sum $M/sb_headacc/*.tar 2>&1
echo "@@@ k1_dirs"; ls -la $R/k1_ops3/work/codex_arkit_timing/ 2>&1 | head -40; ls /scratch/jjyeung/k1 2>&1 | head -60 | tr '\n' ' '; echo; ls -la $R/b10_reserve/out $R/b10_reserve/out/qsets 2>&1 | head -50
echo "@@@ end"
