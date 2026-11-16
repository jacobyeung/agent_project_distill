set -u
X=/scratch/jjyeung/orch_n30/b05_owngrd_x118
cd /scratch/jjyeung
date -u +%FT%TZ > $X/START
cat k1/m544_parts/469ddece_mstop.tar.part0{0,1,2,3}-of-04 | nice -n 10 python3 $X/st_extract.py $X/sub visual embed_tokens > $X/extract.log 2>&1
echo rc=$? >> $X/extract.log
sha256sum $X/sub/* > $X/sub/SHA256SUMS
tar cf - -C $X sub | ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-3-30.ib "mkdir -p /scratch/jjyeung/orch_n30/b05_owngrd/work/m544sub && cd /scratch/jjyeung/orch_n30/b05_owngrd/work/m544sub && tar xf -"
tar cf - -C /scratch/jjyeung/orch_cd/mdg_build/work t0bundle/base weights/resnet18-f37072fd.pth -C /scratch/jjyeung/orch_cd/own_probe/out own_probe_delivery_r3.tar.gz g3t_taps.py room_gate.py API.md P0_CARD.md | ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-3-30.ib "mkdir -p /scratch/jjyeung/orch_n30/b05_owngrd/work/from118 && cd /scratch/jjyeung/orch_n30/b05_owngrd/work/from118 && tar xf -"
echo sent rc=$? >> $X/extract.log
date -u +%FT%TZ > $X/END
