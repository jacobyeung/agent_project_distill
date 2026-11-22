export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1
df -B1G /project/community | tail -1
for d in $X/c_eb8145adr $X/o/174369 $X/o/174246 $X/s29r $X/s29r.tar ~/a15o; do [ -e $d ] && echo "$(timeout 60 du -sB1M $d 2>/dev/null | cut -f1) MiB $d"; done
echo "-- X/u newer than 04:00Z:"; find $X/u -maxdepth 1 -newermt '2026-11-22 04:00' -printf '%s %p\n' 2>/dev/null | head
echo "-- X first level newer than 04:00Z:"; find $X -maxdepth 1 -newermt '2026-11-22 04:00' -printf '%y %s %p\n' 2>/dev/null | head -20
echo "-- home newer:"; find ~ -maxdepth 2 -newermt '2026-11-22 04:00' -printf '%y %s %p\n' 2>/dev/null | head -20
squeue -u jjyeung -h -o '%i|%j|%P|%T|%M|%N'
