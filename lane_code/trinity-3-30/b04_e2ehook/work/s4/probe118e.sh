cat /scratch/jjyeung/envs/sam3_scipy_ovl/lib/python3.12/site-packages/zz_evalx_sam3_overlay.pth
S=/scratch/jjyeung/envs/sam3_capretry_native_v1/lib/python3.12/site-packages
ls $S/*.pth; cat $S/*.pth | head; cat $S/sam3-0.1.0.dist-info/direct_url.json 2>/dev/null; echo
for r in $(cat $S/*.pth 2>/dev/null | grep "^/" ); do [ -f $r/sam3/model_builder.py ] && echo "ROOT $r $(sha256sum $r/sam3/model_builder.py | cut -c1-8) assets=$(ls $r/sam3/assets 2>/dev/null | wc -l)"; done
