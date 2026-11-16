cd /scratch/jjyeung/orch_n30/cont_ops/work/d0 || exit 1
df -h /scratch | tail -1
du -sh readk; ls readk readk/kit | head -60
tar cf - --exclude='*.tar' --exclude='*.safetensors' readk | ssh -o ConnectTimeout=20 trinity-3-30.ib "cd /scratch/jjyeung/orch_n30/b01_d0guard/work/from13 && tar xf -"
echo TAR_RC=$?
