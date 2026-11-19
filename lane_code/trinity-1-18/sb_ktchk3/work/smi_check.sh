#!/usr/bin/env bash
# Check 4 on the reviewed gpu_environment.sh (byte copy from the extracted sb_ktfix4 tar), with fake nvidia-smi readings and a real 300 s wait.
# Busy cases use the real launch path (fake nvidia-smi first on PATH, /usr/bin/sleep) and must refuse before the runner exec;
# a case directory holds no code/runner.py, so a missed refusal cannot reach a GPU. Idle cases use fixture mode, which exits before the runner.
set -uo pipefail
W=/scratch/jjyeung/orch_n30/sb_ktchk3/work
SRC=$W/ex4/scripts/gpu_environment.sh
S=$W/smi
mkdir -p $S
make_case() {  # name memory1 memory2 apps1 apps2
 local R=$S/$1; mkdir -p $R/scripts $R/runtime/fx $R/fakebin
 cp $SRC $R/scripts/gpu_environment.sh
 printf '%s\n%s\n' "$2" "$3" > $R/runtime/fx/memory.txt
 printf '%s\n%s\n' "$4" "$5" > $R/runtime/fx/apps.txt
 cat > $R/runtime/fx/nvidia-smi <<'EOF'
#!/usr/bin/env bash
D=/FXDIR
printf '%s %s | %s | %s|%s\n' "$(date -u +%s)" "$(date -u +%T)" "$*" "$CUDA_DEVICE_ORDER" "$CUDA_CACHE_PATH" >> $D/calls.txt
[[ "$1" == -i && "$2" == 3 ]] || exit 7
if [[ "$3" == --query-gpu=memory.used,utilization.gpu ]]; then
 n=0; [[ -f $D/count ]] && read -r n < $D/count; n=$((n+1)); echo $n > $D/count
 sed -n "${n}p" $D/memory.txt
else
 read -r n < $D/count; sed -n "${n}p" $D/apps.txt
fi
EOF
 sed -i "s#/FXDIR#$R/runtime/fx#" $R/runtime/fx/nvidia-smi
 printf '#!/usr/bin/env bash\necho "sleep $* start $(date -u +%%s)" >> %s/wait.txt\n/usr/bin/sleep "$@"\necho "sleep end $(date -u +%%s)" >> %s/wait.txt\n' $R/runtime/fx $R/runtime/fx > $R/runtime/fx/sleep
 chmod +x $R/runtime/fx/nvidia-smi $R/runtime/fx/sleep
 ln -sf $R/runtime/fx/nvidia-smi $R/fakebin/nvidia-smi
}
run_real() {
 local R=$S/$1
 ( cd $R && PATH=$R/fakebin:$PATH CUDA_VISIBLE_DEVICES=3 nice -n 10 bash scripts/gpu_environment.sh A > $R/stdout.txt 2> $R/stderr.txt; echo $? > $R/rc.txt ) &
}
run_fixture() {
 local R=$S/$1
 ( cd $R && CUDA_VISIBLE_DEVICES=3 nice -n 10 bash scripts/gpu_environment.sh A --test-fixture $R/runtime/fx > $R/stdout.txt 2> $R/stderr.txt; echo $? > $R/rc.txt ) &
}
REAL="busy_first busy_second over_1GiB compute_process padded_first padded_second padded_1025"
FIX="idle_1024 idle_1024_padded padded_fixture padded_1024_1"
make_case busy_first       '20000, 98'   '0, 0'        '4242' ''
make_case busy_second      '0, 0'        '20000, 98'   ''     '4242'
make_case over_1GiB        '1025, 0'     '1025, 0'     ''     ''
make_case compute_process  '0, 0'        '0, 0'        '4242' '4242'
make_case padded_first     ' 10000, 0'   '0, 0'        ''     ''
make_case padded_second    '0, 0'        '10000 , 0'   ''     ''
make_case padded_1025      ' 1025 , 0'   ' 1025 , 0'   ''     ''
make_case idle_1024        '1024, 0'     '0, 0'        ''     ''
make_case idle_1024_padded ' 1024 , 0'   ' 0 , 0'      ''     ''
make_case padded_fixture   ' 10000, 0'   '10000 , 0'   ''     ''
make_case padded_1024_1    ' 1024.1 , 0' '0, 0'        ''     ''
cmp $SRC $S/busy_first/scripts/gpu_environment.sh && sha256sum $SRC
date -u +%T; for c in $REAL; do run_real $c; done; wait
date -u +%T; for c in $FIX; do run_fixture $c; done; wait
date -u +%T
for c in $REAL $FIX; do
 R=$S/$c; echo "== $c rc=$(cat $R/rc.txt) stderr=$(tr '\n' ' ' < $R/stderr.txt)"
 awk '{print "   call", $0}' $R/runtime/fx/calls.txt
 [[ -f $R/runtime/fx/wait.txt ]] && awk '{print "   wait", $0}' $R/runtime/fx/wait.txt
 L=$(ls $R/out/tower_frames/NVIDIA_SMI_A.log $R/runtime/fx/out/tower_frames/NVIDIA_SMI_A.log 2>/dev/null); echo "   log $L readings=$(grep -c '^Reading' $L)"
done
