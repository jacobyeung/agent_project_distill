export PATH=/cm/shared/apps/slurm/current/bin:$PATH
B=/lustre/fsw/portfolios/av/users/jyeung/ap/59845bf9
F=$B/d/orch/runs/aws128p_20261025/frozen
timeout 60 lfs quota -u jyeung /lustre/fsw 2>/dev/null | awk '$1 == "/lustre/fsw" {printf "QUOTA_FILES used=%s free=%d\n", $6, $8 - $6}'
sacct -j 8428164,8428165,8428268 -X -P -n -o JobID,State,Elapsed 2>/dev/null | sed 's/^/JOB /'
for a in RG1_X_S17_K200 R27_X_S17_K200; do [ -f $F/$a/ADMISSION.json ] && grep -q CPU_ADMISSION_OK $F/$a/ADMISSION.json && echo "K200ADMITTED $a"; done
for a in RG1_X_W64_S17_K200 RG1_X_W64_S18_K200 RG1_A1S_W64_S17_K200; do echo "COUNT $a top=$(ls -A $F/$a | wc -l)"; done
grep -h "^PACKED\|^PACK_FAILED\|^PACK_DONE" $B/l/a15_cot_ap0081f0ca_8428268.log 2>/dev/null
true
