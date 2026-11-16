cd /scratch/jjyeung/orch_n30/native_r2 || exit 1
tar cf - builds/01_c8 work/obj work/np226 work/pyextra work/p9 work/wheels work/meta work/direct | ssh -o ConnectTimeout=20 trinity-3-30.ib "cd /scratch/jjyeung/orch_n30/b01_d0guard/work/from113 && tar xf -"
echo TAR_RC=$?
