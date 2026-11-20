cd /scratch/jjyeung/distill_sync/repo
git diff-tree -r --no-renames --diff-filter=AM bcd2342f~1 bcd2342f | awk '{print $4" "$5" "$6}' > /tmp/sm_m3.txt
awk '{print $1}' /tmp/sm_m3.txt | git cat-file --batch-check='%(objectsize)' | paste -d' ' - /tmp/sm_m3.txt > /tmp/sm_m3s.txt
awk '{s[$3]+=$1; n[$3]++} END{for(k in s) print k, n[k], s[k]}' /tmp/sm_m3s.txt
awk '$3=="A"{split($4,a,"/"); k=a[2]"/"a[3]"/"a[4]"/"a[5]; s[k]+=$1} END{for(k in s) print s[k], k}' /tmp/sm_m3s.txt | sort -nr | head -12
awk '$3=="M"{split($4,a,"/"); k=a[2]"/"a[3]"/"a[4]"/"a[5]; s[k]+=$1} END{for(k in s) print s[k], k}' /tmp/sm_m3s.txt | sort -nr | head -6
