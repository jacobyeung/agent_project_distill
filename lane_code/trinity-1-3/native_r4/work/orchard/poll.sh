export TZ=UTC
date -u +%FT%TZ
squeue -j 170209 -h -o '%i %T %M %l %S %N %r' 2>&1
sacct -j 170209 -X -n -o State,Elapsed,Start,End,ExitCode 2>&1 | head -2
ls -la /project/community/jjyeung/okh7/n2r/ece5eea1c1ec94e169abf835 2>/dev/null | head
if [ "$(squeue -j 170209 -h -o %T)" = RUNNING ]; then
  timeout 60 srun --jobid=170209 --overlap --ntasks=1 --cpus-per-task=1 --mem=1G --gres=none bash -c 'R=$(ls -d /tmp/a15_170209_* 2>/dev/null|head -1); echo root $R; tail -c 600 $R/staging.log 2>/dev/null; echo; find $R/run -maxdepth 3 2>/dev/null | head -40; tail -c 1500 $R/b.log 2>/dev/null; ls $R/run/p 2>/dev/null; cat $R/run/p/PROOF.json 2>/dev/null | head -c 1500; ls $R/run/j0 2>/dev/null | head' 2>&1 | head -80
fi
