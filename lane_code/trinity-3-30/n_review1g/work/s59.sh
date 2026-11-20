W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; Y=$W/w24y2; Z=$W/w24z4; P=/scratch/jjyeung/envs/p1cpu/bin/python; N=/scratch/jjyeung/orch_n30/n_review; R=$N/r1g; T=$N/r1f/tcpx
echo "== identity"
k=$Z/out/kit_n_go
nice -n 10 bwrap --ro-bind / / --tmpfs /home --tmpfs /data --tmpfs /data2 --tmpfs /data3 --tmpfs /scratch/jjyeung --ro-bind /scratch/jjyeung/envs/p1cpu /scratch/jjyeung/envs/p1cpu --ro-bind /scratch/jjyeung/uv-python /scratch/jjyeung/uv-python --tmpfs /tmp --ro-bind $T /tmp/x/tree --ro-bind $k/k /tmp/x/k --ro-bind $N/r1e/ident2.py /tmp/x/ident2.py --dev /dev --proc /proc --unshare-net --chdir /tmp/x env -i PATH=/usr/bin:/bin OMP_NUM_THREADS=2 $P -I -s -B /tmp/x/ident2.py > $R/ident_w24z4_tcpx.json 2>&1 < /dev/null
sha256sum $N/r1e/ident2.py $R/ident_w24z4_tcpx.json; grep -o '"[a-z_]*identity[a-z_]*": *"[0-9a-f]*"\|"[a-z_]*sha256": *"[0-9a-f]*"' $R/ident_w24z4_tcpx.json | head -8
head -c 1500 $R/ident_w24z4_tcpx.json; echo; grep -o "4794b27f[0-9a-f]*\|a1fd8b40[0-9a-f]*\|6d6fda1b[0-9a-f]*" $R/ident_w24z4_tcpx.json | sort | uniq -c
J=$W/w24z/work/enospc/decoded_j.sh; echo "== Q_ROOT / pc.sh in j.sh"; grep -n 'Q_ROOT=\|N=\|pc\.sh\|ROOT=' $J | head -20
ls $Z/out | grep -i 'ENOSPC\|E2\|SESS\|UPLOAD' ; M=$Z/out/ENOSPC_24M4Z4.md; sha256sum $M; grep -n -i 'stop checkpoint\|size\|rate\|MB/s\|GiB\|Q_ROOT\|rooms_rc\|order\|archive' $M | cut -c1-400 | head -60
