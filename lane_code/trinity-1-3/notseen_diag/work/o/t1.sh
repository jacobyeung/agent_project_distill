cd /scratch/jjyeung/orch_n30/native_r2/work || exit 1
hostname; df -h /scratch | tail -1
ls -la . obj full_c8r 2>&1 | head -60
T=obj/masks_4984fac22d84e8c5.tar
ls -la $T
tar tvf $T > /tmp/nsd_t1_list.txt 2>&1; wc -l /tmp/nsd_t1_list.txt
awk '{print $3, $6}' /tmp/nsd_t1_list.txt | grep -v -E '\.(png|jpg|npz|npy)$' | head -120
awk '{print $6}' /tmp/nsd_t1_list.txt | awk -F/ '{print $1"/"$2"/"$3"/"$4}' | sort | uniq -c | sort -rn | head -30
for f in full_c8r/*; do echo "== $f"; done
ls -la full_c8r/* 2>&1 | head -30
