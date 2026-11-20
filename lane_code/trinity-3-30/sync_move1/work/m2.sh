R=/scratch/jjyeung/distill_sync/repo
cd $R && git log --format='%h %cI %s' -3
for c in bcd2342f 5bb86699; do git diff-tree -r --no-renames --diff-filter=AM $c~1 $c | awk '{print $4}' | git cat-file --batch-check='%(objectsize)' | awk -v c=$c '{s+=$1;n++} END{print c, "added_or_modified_files="n, "bytes="s}'; done
git diff-tree -r --no-renames --diff-filter=AM bcd2342f~1 bcd2342f | awk '{print $4" "$6}' > /tmp/sm_m2.txt; awk '{print $1}' /tmp/sm_m2.txt | git cat-file --batch-check='%(objectsize)' | paste -d' ' - /tmp/sm_m2.txt | awk '{split($3,a,"/"); k=a[2]"/"a[3]; s[k]+=$1} END{for(k in s) print s[k], k}' | sort -nr | head -8
grep -E "STATS|committed|SKIP|FAIL" $S/sync.log 2>/dev/null | tail -0
grep -E "^\s+\[copy [^]]+\] STATS|committed|FAIL|SKIP" /scratch/jjyeung/distill_sync/sync.log | tail -7 | cut -c1-160
du -sh $R/.git; df -h /scratch | tail -1
