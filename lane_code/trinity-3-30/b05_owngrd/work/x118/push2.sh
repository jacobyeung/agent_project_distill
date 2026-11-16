cat > /scratch/jjyeung/orch_n30/b05_owngrd/work/x118/launch_teacher.sh <<"SHEOF"
# Usage on trinity-1-18 (after ORCH_CARD): bash launch_teacher.sh <card> <shard i/n>
set -eu
CARD=$1; SHARD=$2; L=/scratch/jjyeung/orch_n30/b05_owngrd; OUT=/scratch/jjyeung/orch_n30/b05_owngrd/teacher_k1
mkdir -p $OUT; cd $L/code
cat > $L/work/x118/settings_gpu.json <<SEOF
{"checkpoint_path": "/scratch/jjyeung/orch_cd/ttower/work/sam3_weights/sam3.pt", "receipt_path": "$L/code/owngrd/vendor/SAM3_RECEIPT.json", "source_root": "/scratch/jjyeung/orch_cd/mdg_next/work/data/sam3src", "device": "cuda", "precision": "bf16"}
SEOF
SHA=$(sha256sum $L/work/manifests/TEACHER_K1.json | cut -d' ' -f1)
TAG=$(echo $SHARD | tr / o)
tmux new-session -d -s b05_teacher_$TAG "cd $L/code && CUDA_VISIBLE_DEVICES=$CARD XDG_CACHE_HOME=/scratch/jjyeung/.cache TORCH_HOME=/scratch/jjyeung/.cache/torch /data3/shared/scripts/vnice/vnice.sh /scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python -m owngrd.teacher --manifest $L/work/manifests/TEACHER_K1.json --manifest-sha256 $SHA --out $OUT --settings $L/work/x118/settings_gpu.json --shard $SHARD --hours 8 > $OUT/worker_$TAG.log 2>&1; echo rc=\$? >> $OUT/worker_$TAG.log"
echo launched b05_teacher_$TAG card $CARD
SHEOF
ls -la /scratch/jjyeung/orch_n30/b05_owngrd/work/x118/; ls /data3/shared/scripts/vnice/vnice.sh; which tmux
