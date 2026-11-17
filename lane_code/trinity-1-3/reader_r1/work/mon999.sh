export TZ=UTC; date -u +%FT%TZ
squeue -j 170999 -h -o '%i %P %T %M %R'; sacct -j 170999 -n -X -o state,elapsed,exitcode | head -1
tail -4 /project/community/jjyeung/c3cc59fb4aae0/a/cpu_check.log 2>/dev/null
ls /project/community/jjyeung/c3cc59fb4aae0/a/c 2>/dev/null
