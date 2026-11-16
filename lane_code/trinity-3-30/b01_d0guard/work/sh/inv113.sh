cd /scratch/jjyeung/orch_n30/native_r2 || exit 1
df -h /scratch | tail -1
ls sub/ builds/ work/ 
du -sh sub builds/02_c8r builds/01_c8 work/obj work/full_c8r env312 work/code9 work/base work/tree 2>/dev/null
ls -la sub/b07a20b364/ builds/02_c8r builds/02_c8r/out builds/02_c8r/work 2>/dev/null | head -80
ls -la work/obj work/full_c8r | head -40
