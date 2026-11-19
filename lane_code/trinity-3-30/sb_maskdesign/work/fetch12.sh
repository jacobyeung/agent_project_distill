V=/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a/native_kit/vendor_sam/vendor
echo "=== receipt"; cat $V/SAM3_RECEIPT.json; echo
echo "=== sha ckpts"; for f in /scratch/jjyeung/allospatial_build_1111_v1/package_v5p1/models/sam3.pt /scratch/jjyeung/b01ec87a6f29b/d/k/sam3.pt; do ls -la $f; nice -n 10 sha256sum $f; done
echo "=== staged source roots"; for d in /scratch/jjyeung/split_efficiency/sam3/home /scratch/jjyeung/b01ec87a6f29b/d /scratch/jjyeung/trinity_qwen_sam3 /scratch/jjyeung/allospatial_build_1111_v1/package_v5p1; do echo "-- $d"; find $d -maxdepth 7 -name model_builder.py 2>/dev/null | head -5; done
ls /scratch/jjyeung/b01ec87a6f29b/d | head -20; ls /scratch/jjyeung/b01ec87a6f29b/d/k | head -20
echo "=== reader tower settings"; grep -rnE "source_root|checkpoint_path|receipt_path" /scratch/jjyeung/orch_n30/b04host3/b04_e2ehook/*.py /scratch/jjyeung/orch_n30/b04host3/b04_e2ehook/e2e_reader/*.py 2>/dev/null | cut -c1-260 | head -14
