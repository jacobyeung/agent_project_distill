hostname
P=/scratch/jjyeung/orch_n30/rows_rebuild/work/pull/pool
ls -l $P 2>&1 | head -20
for h in 6053fd47c70c0b25 7a1c59097139f59d 7e4e92918e312afd 9bf0518db09a07d8 9eecedf23da3bd91 b6ac18d55d697a23 ba96a4182147a384 c16c5db36e04c1ef; do [ -f $P/$h.jsonl.gz ] && sha256sum $P/$h.jsonl.gz; done
R=/scratch/jjyeung/orch_n30/rows_a2/work/rasters
ls $R 2>&1 | wc -l; du -sh $R 2>&1 | tail -1
ls -d /scratch/jjyeung/orch_cd /scratch/jjyeung/orch_n30/*/work/weak_data 2>&1 | head -3
