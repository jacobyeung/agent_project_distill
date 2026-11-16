export TZ=UTC; date -u +%FT%TZ
squeue -j 170379 -h -o '%i %T %M %N'; cat /project/community/jjyeung/okh7/db3954b2/logs/dserial.170379.log; tail -5 /project/community/jjyeung/okh7/db3954b2/logs/a0n3.170379t0_0.log
