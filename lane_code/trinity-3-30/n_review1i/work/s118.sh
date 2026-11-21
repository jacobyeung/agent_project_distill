K=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w26fix2/n_go
sed -n 495,530p $K/b/z.py < /dev/null | cut -c1-260
echo "== pl.py root/u"; grep -n "'u'\|/'u'\|\"root\"\|\['root'\]" $K/b/pl.py $K/b/z.py < /dev/null | cut -c1-220 | head -20
