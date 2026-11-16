set +e
cd /scratch/jjyeung/orch_n30/native_r2 || exit 3
ip route get $(getent hosts trinity-1-3.ib | awk '{print $1}') | head -1
time (tar cf - work/obj builds/02_c8r sub work/tree work/full_c8r work/rec work/pyextra work/meta work/code9 env312 STATUS.md | timeout 1200 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-1-3.ib 'cd /scratch/jjyeung/orch_n30/native_r4/from113 && tar xf - && echo XF_OK')
cd work/obj && sha256sum frames.tar geometry_8c58df1547371bdb.tar np226_5204b3a0.tar t_b01ce449beffe35b.tar metadata_e10fbb95487f3baf.tar masks_4984fac22d84e8c5.tar
