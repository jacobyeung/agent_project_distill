export TZ=UTC; date -u +%FT%TZ
sacct -j 170377 -X -n -o JobID,State,ExitCode,Start,End,NodeList%30 2>&1
cat /project/community/jjyeung/okh7/db3954b2/logs/egress.170377.json 2>&1; echo; cat /project/community/jjyeung/okh7/db3954b2/logs/disk.170377.txt 2>&1 | head -40; nproc 2>/dev/null
