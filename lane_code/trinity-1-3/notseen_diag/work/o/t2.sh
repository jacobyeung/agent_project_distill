cd /scratch/jjyeung/orch_n30/native_r2/work || exit 1
sort -k3 -n -r /tmp/nsd_t1_list.txt | awk '{print $3, $6}' | head -25
awk '{print $6}' /tmp/nsd_t1_list.txt | sed -E 's/.*\.([a-z0-9]+)$/\1/' | sort | uniq -c
grep -v candidates /tmp/nsd_t1_list.txt | awk '{print $3, $6}' | head -40
ls -laR full_c8r/x | head -60
tar tzvf full_c8r/result.tar.gz | awk '{print $3, $6}' | head -60
cat full_c8r/SIDE_BY_SIDE.md | head -60
