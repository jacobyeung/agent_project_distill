export TZ=UTC; date -u
P=/project/community/jjyeung/okh7/b7e31d84a90c62f5
squeue -j 170235 -h -o '%i %T %M %l %R %S' 2>&1
sacct -j 170235 -X -n --format=State,ExitCode,Elapsed,Start,NodeList 2>&1
ls -la $P/170235/ 2>&1; for d in $P/170235/*/; do [ -d "$d" ] && ls -la "$d"; done 2>/dev/null
D=$P/170235/c75955208369b4e48; tar tvzf $D/result.tar.gz | awk '{s+=$3} END {print "canary_uncompressed_bytes", s}'
