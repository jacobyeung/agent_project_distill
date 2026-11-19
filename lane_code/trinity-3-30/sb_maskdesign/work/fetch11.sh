SP=/scratch/jjyeung/envs/sam3_capretry_native_v1/lib/python3.12/site-packages
echo "=== finder mapping"; grep -n "MAPPING" $SP/__editable___sam3_0_1_0_finder.py | cut -c1-300 | head -3
SRC=$(grep -oE "'sam3': '[^']+'" $SP/__editable___sam3_0_1_0_finder.py | head -1 | grep -oE "'/[^']+'" | tr -d "'"); echo "SRC=$SRC"
[ -d "$SRC" ] && { ls $SRC | head -40; echo "-- model"; ls $SRC/model 2>/dev/null | head -60; echo "-- train"; ls $SRC/train 2>/dev/null | head -30; ls $SRC/train/loss 2>/dev/null | head; grep -n "def build_sam3" $SRC/model_builder.py 2>/dev/null | cut -c1-200; }
echo "=== ckpt"; ls -la /scratch/jjyeung/split_efficiency/sam3/sam3_ckpt 2>&1 | head; ls -la /dev/shm/jjyeung* 2>/dev/null | head -20
V=/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a/native_kit/vendor_sam/vendor
echo "=== vendor"; ls -la $V | head -20; grep -nE "sam3\.pt|checkpoint|ckpt|SAM3_|environ" $V/sam_backend.py $V/sam3_tower.py 2>/dev/null | cut -c1-220 | head -30
echo "=== k1 run2 launch"; ls /scratch/jjyeung/k1/tools | head -20; grep -rnE "sam3|SAM3" /scratch/jjyeung/k1/tools/*.sh /scratch/jjyeung/k1/*.json 2>/dev/null | cut -c1-260 | head -12
echo "=== locate sam3.pt (bounded)"; ls -la /scratch/jjyeung/sam3* /scratch/jjyeung/models 2>/dev/null | head -20; ls -d /scratch/jjyeung/*/sam3.pt /scratch/jjyeung/*/*/sam3.pt /scratch/jjyeung/*/*/*/sam3.pt 2>/dev/null | head
