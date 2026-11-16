B=/dev/shm/jjyeung/b04/host; L=$B/b04_e2ehook; T=$B/tree_rebuild/work/base/tree_b01ce449
PY=/scratch/jjyeung/envs/vllm/bin/python; OV=/dev/shm/jjyeung/b04/pyoverlay; SP=/dev/shm/jjyeung/b05/stage/sam3_capretry_native_v1/lib/python3.12/site-packages
for p in iopath portalocker ftfy regex timm einops pycocotools; do
  if PYTHONPATH=$OV $PY -c "import $p" 2>/dev/null; then echo "have $p"; else (cd $SP && tar cf - $p $p-*.dist-info 2>/dev/null) | tar xf - -C $OV && echo "copied $p"; fi
done
cd $L && PYTHONPATH=$OV timeout 120 $PY -B -m parity_kit.sam3_probe --source-root /dev/shm/jjyeung/b05/stage/sam3src --checkpoint /dev/shm/jjyeung/b05/stage/sam3.pt --tree $T 2>&1 | grep -v Warn | tail -16
