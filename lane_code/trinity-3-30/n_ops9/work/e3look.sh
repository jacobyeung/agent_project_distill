D=/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/d173966/173966
ls -la $D 2>&1 | head; ls /scratch/jjyeung/orch_n30/tree_rebuild10_w/work/ 2>&1 | grep -i 173966
f=$(ls $D/logs.tgz 2>/dev/null || ls /scratch/jjyeung/orch_n30/tree_rebuild10_w/W/work/d173966/173966/logs.tgz 2>/dev/null)
echo "== $f"; tar tzvf $f 2>&1 | head -40
for m in $(tar tzf $f 2>/dev/null | grep -i -E 'upload|attempt|u\.log|gc\.' | head -4); do echo "=== $m"; tar xzOf $f $m | sed -E 's#https://[^ "]*#<URL>#g; s#(upload_id|session)[^ ,]*#\1=<masked>#g' | head -12 | cut -c1-400; done
