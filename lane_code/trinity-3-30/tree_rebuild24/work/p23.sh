W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; Z=$W/w24z10/out; date -u +%TZ; P=$Z/tree_rebuild_b24m4z10_1c7d7c1e.tar
cut -c1-16 $P.sha256; sha256sum $P | cut -c1-16
cat $Z/BUILD24M4Z10_REPORT.md; echo ==NEEDS; cat $Z/NEEDS_OTHER_FILE_24M4Z10.md; echo ==ENOSPC; cat $Z/ENOSPC_24M4Z10.md
ls $Z $Z/e3 $Z/tgcs; sha256sum $Z/kit_n/k/y.json $Z/kit_n_go/k/y.json $Z/kit_n/b/gc.py | cut -c1-90; grep -n "HTTPSConnection" $Z/tgcs/observe.py $Z/e3/observe.py
timeout 300 bash -c "cat $P | ssh -o ConnectTimeout=20 trinity-2-28.ib 'cat > /scratch/jjyeung/n30_mirror/tree_rebuild23/$(basename $P) && sha256sum /scratch/jjyeung/n30_mirror/tree_rebuild23/$(basename $P) | cut -c1-16'" < /dev/null
