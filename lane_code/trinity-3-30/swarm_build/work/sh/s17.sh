R=/scratch/jjyeung/orch_n30/sb_scale2; wc -c $R/out/SCALE_DRIFT_REPORT.md; sha256sum $R/out/SCALE_DRIFT_REPORT.md $R/out/SCALE_DRIFT.json | cut -c1-16; cat $R/out/SCALE_DRIFT_REPORT.md
