#!/bin/bash
# one-time prep on trinity-1-18: overlay env, restore + manifest, SAM 3 probe, one CPU camera item (SAM 3 off)
H=/scratch/jjyeung/orch_n30/b04host3; L=$H/b04_e2ehook; LOG=$L/work/prep118.log; mkdir -p $L/work
{
echo "$(date -u +%FT%TZ) PREP start"
OV=$H/pyoverlay; mkdir -p $OV
P=$(ls -d /scratch/jjyeung/envs/p1cpu/lib/python3*/site-packages); S=/scratch/jjyeung/envs/sam3_capretry_native_v1/lib/python3.12/site-packages
cp -a $P/scipy $P/scipy.libs $P/scipy-1.14.1.dist-info $OV/ 2>&1
for p in iopath portalocker ftfy timm pycocotools wcwidth; do cp -a $S/$p $S/$p-*.dist-info $OV/ 2>&1; done
ls $OV | tr '\n' ' '; echo
bash $L/parity_kit/gpu_inner_118.sh none own_depth prep; echo "PREP_RC=$?"
cd $L && PYTHONPATH=$OV /scratch/jjyeung/envs/vllm/bin/python -B -m parity_kit.sam3_probe --source-root /scratch/jjyeung/orch_cd/mdg_next/work/data/sam3src --checkpoint /scratch/jjyeung/orch_cd/ttower/work/sam3_weights/sam3.pt --tree $H/tree_rebuild/work/base/tree_b01ce449 2>&1 | tail -20; echo "PROBE_RC=$?"
head -1 $L/parity_kit/keys_smoke.txt > $L/work/key_cam1.txt
bash $L/parity_kit/gpu_inner_118.sh cpu own_depth cpu_cam1_118 $L/work/key_cam1.txt 2>&1 | grep -v -i "warn\|fast path" | tail -20; echo "CPU_RC=$?"
echo "$(date -u +%FT%TZ) PREP end"
} >> $LOG 2>&1
