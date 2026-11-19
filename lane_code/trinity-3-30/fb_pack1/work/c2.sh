F=/scratch/jjyeung/orch_n30/fb_pack; ls -la $F/patchA/out/fbp_patchA.tar; du -sh $F/patchA/out
cd $F/patchA && tar cf - --exclude='fbp_patchA.tar' out work/*.py 2>/dev/null | ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-1-18.ib "mkdir -p $F/patchA_out && cd $F/patchA_out && tar xf - && du -sh . && sha256sum out/PATCH_A.patch"
sha256sum out/PATCH_A.patch
