F=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24f; R=$F/rehearsal4
date -u +%TZ
ls -la $R/train $R/p2 | head -60
for f in VIEW.json LAUNCH_CHANGES.json FINAL_VALIDATION.json; do echo "@@@ $f $(sha256sum <$R/$f|cut -c1-64)"; head -c 2500 $R/$f; echo; done
for f in train_fresh.log train_budget.log train_resume.log; do echo "@@@ $f $(stat -c %s $R/$f) $(sha256sum <$R/$f|cut -c1-64)"; grep -a -E 'stop_reason|checkpoint|"step": ?1[,}]|budget|resume|export|Error|error|last_step' $R/$f | cut -c1-300 | head -40; done
ls $R/train/*.json* 2>/dev/null; for f in $R/train/run_*.json $R/train/attempt_*.json; do [ -f $f ] && { echo "@@@ $f"; head -c 1500 $f; echo; }; done
for f in $R/train/metrics_*.jsonl; do [ -f $f ] && { echo "@@@ $f $(wc -l <$f)"; cut -c1-200 $f | head -12; }; done
R5=$F/rehearsal5; ls -la $R5 | head -60
find $R5/target -maxdepth 5 -name 'gcs_*' -exec sh -c 'echo "@@@ $1"; cat "$1"; echo' _ {} \;
echo "@@@ r5 train_budget"; grep -a -E 'Error|error|refus|stop_reason|R1_|E[0-9]+' $R5/train_budget.log | cut -c1-400 | tail -25
