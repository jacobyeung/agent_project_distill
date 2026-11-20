cd /scratch/jjyeung/orch_n30/sb_own400 || exit 1
ls -la . kit out in | head -80
echo ==== KIT_REPORT_B; cat KIT_REPORT_B.md 2>/dev/null || ls kit/*REPORT* out/*REPORT* 2>/dev/null
echo ==== fov_variants; wc -c kit/fov_variants.py; cat kit/fov_variants.py
df -h /scratch | tail -1
