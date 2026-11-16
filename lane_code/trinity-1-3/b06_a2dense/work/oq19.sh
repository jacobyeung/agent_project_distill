export TZ=UTC; date -u +%FT%TZ
squeue -j 170374 -h -o '%i %T %S %M' 2>&1; sacct -j 170374 -X -n -o JobID,State,ExitCode,Start,End,NodeList 2>&1
ls -la /project/community/jjyeung/okh7/db3954b2/logs/ | tail -5; cat /project/community/jjyeung/okh7/db3954b2/logs/egress.170374.json 2>&1; echo; cat /project/community/jjyeung/okh7/db3954b2/logs/disk.170374.txt 2>&1 | head -40
