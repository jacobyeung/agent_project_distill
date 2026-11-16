set -u
B=/scratch/jjyeung/orch_n30/b04host; L=$B/b04_e2ehook
sha256sum $L/parity_kit/build_manifest.py
PY=/scratch/jjyeung/envs/p1cpu/bin/python; T=$B/tree_rebuild/work/base/tree_b01ce449; O=$L/parity_kit/host_restore; R=$L/parity_kit/host_results
cat > $L/work/host_run2.sh <<SH
set -u
cd $L
export PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TMPDIR=$L/work/tmp OMP_NUM_THREADS=32
mv $L/parity_kit/E2E_MANIFEST.json $L/parity_kit/E2E_MANIFEST.v1.json; mv $L/parity_kit/E2E_MANIFEST.binding.json $L/parity_kit/E2E_MANIFEST.binding.v1.json
nice -n 10 $PY -B -m parity_kit.build_manifest --root /scratch/jjyeung --export-dir $O --g3t /scratch/jjyeung/k1/g3t --selector-head $L/heads/selector/work/run_iso --scale-head $L/heads/scale/work/run1 --code reader=$L/e2e_reader --code tree=$T --code heads=$L/heads --out $L/parity_kit/E2E_MANIFEST.json > $L/work/manifest2.log 2>&1; echo MANIFEST_RC=\\\$? >> $L/work/manifest2.log
nice -n 10 $PY -B -m parity_kit.cpu_first_batch --settings $L/parity_kit/settings.json --arm own_depth --device cpu --out $R/cpu_first2 > $L/work/first2.log 2>&1; echo FIRST_RC=\\\$? >> $L/work/first2.log
SH
tmux new-session -d -s b04_host2 "bash $L/work/host_run2.sh"
# stage for 1-13 (ORCH 1504Z yes): frames + G3T + code + scipy overlay into /dev/shm/jjyeung/b04
SP=/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages
cat > $L/work/stage113.sh <<SH
set -u
cd /scratch/jjyeung && tar cf - devs1_frames k1/g3t | timeout 1800 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-1-13.ib 'mkdir -p /dev/shm/jjyeung/b04 && tar xf - -C /dev/shm/jjyeung/b04 && echo FRAMES_G3T_OK'
cd $B && tar cf - --exclude=b04_e2ehook/parity_kit/host_restore --exclude='b04_e2ehook/parity_kit/host_results*' --exclude=b04_e2ehook/parity_kit/settings.json --exclude='b04_e2ehook/parity_kit/E2E_MANIFEST*' b04_e2ehook tree_rebuild | timeout 900 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-1-13.ib 'mkdir -p /dev/shm/jjyeung/b04/host && tar xf - -C /dev/shm/jjyeung/b04/host && echo CODE_OK'
cd $SP && tar cf - scipy scipy.libs scipy-*.dist-info 2>/dev/null | timeout 900 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-1-13.ib 'mkdir -p /dev/shm/jjyeung/b04/pyoverlay && tar xf - -C /dev/shm/jjyeung/b04/pyoverlay && echo SCIPY_OK; du -sh /dev/shm/jjyeung/b04; sha256sum /dev/shm/jjyeung/b04/k1/g3t/model.safetensors'
SH
tmux new-session -d -s b04_stage113 "bash $L/work/stage113.sh > $L/work/stage113.log 2>&1"
sleep 3; tmux ls | grep b04
