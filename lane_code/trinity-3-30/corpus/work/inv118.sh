hostname -s; df -BG --output=avail /scratch | tail -1
cd /scratch/jjyeung || exit 1
ls n30_mirror; echo ---; ls n30_mirror/cont_ops | head -50; echo ---
du -sh n30_mirror/* 2>/dev/null
echo --- old_lanes
ls -la n30_mirror/old_lanes_3_30 2>/dev/null | head -40
echo --- k1_ops3
ls -d /scratch/jjyeung/*k1_ops3* /scratch/jjyeung/orch_n30/k1_ops3 n30_mirror/k1_ops3 2>/dev/null; du -sh /scratch/jjyeung/orch_n30/k1_ops3 2>/dev/null
echo --- markers
for d in n30_mirror/cont_ops /scratch/jjyeung/orch_n30/k1_ops3 n30_mirror/k1_ops3; do [ -d $d ] && find $d \( -name FETCH.json -o -name "result*.tar.gz" -o -name "items_a0.jsonl" -o -name "items.jsonl*" -o -name "*.tar" \) -printf "%s %p\n" 2>/dev/null | grep -v -E "evidence/test_|test_tmp|pytest|/tests?/|chain_" ; done | awk '{printf "%.1fM %s\n",$1/1e6,$2}' | head -300
