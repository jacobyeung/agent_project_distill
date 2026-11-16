export TZ=UTC
date -u +%FT%TZ
squeue -j 170228 -h -o '%i %T %M %l %S %N %r' 2>&1
sacct -j 170228 -X -n -o State,Elapsed,Start,End,ExitCode 2>&1 | head -2
ls -la /project/community/jjyeung/okh7/n2r/8f7817fb16bc218af285dc61 2>/dev/null | head
if [ "$(squeue -j 170228 -h -o %T)" = RUNNING ]; then
  timeout 60 srun --jobid=170228 --overlap --ntasks=1 --cpus-per-task=1 --mem=1G --gres=none bash -c 'R=$(ls -d /tmp/a15_170228_* 2>/dev/null|head -1); echo root $R; tail -c 600 $R/staging.log 2>/dev/null; echo; find $R/run -maxdepth 2 -not -path "*/store*" 2>/dev/null | sed "s#$R/run/##" | tr "\n" " "; echo; echo g_files $(find $R/run/cell -type f 2>/dev/null | wc -l) $(du -sm $R/run/cell 2>/dev/null | cut -f1)MB; echo PHASES; head -c 1500 $R/run/PHASES.json 2>/dev/null; echo; for j in $R/run/j*; do [ -d $j ] && echo "$j $(ls $j | wc -l) files"; done; tail -c 1200 $R/b.log | tr -c "[:print:]\n" " " 2>/dev/null; ls $R/run/p 2>/dev/null; cat $R/run/p/PROOF.json 2>/dev/null | head -c 1500; ls $R/run/j0 2>/dev/null | head' 2>&1 | head -80
fi
if [ "$(squeue -j 170228 -h -o %T)" = PENDING ]; then NOW=$(date -u +%s); END=$(date -u -d 2026-11-16T16:30:00Z +%s); MIN=$(( (END-NOW)/60 )); TL=$(printf '%02d:%02d:00' $((MIN/60)) $((MIN%60))); scontrol update JobId=170228 TimeLimit=$TL && echo "limit lowered to $TL"; squeue -j 170228 -h -o '%T %l %r'; fi
