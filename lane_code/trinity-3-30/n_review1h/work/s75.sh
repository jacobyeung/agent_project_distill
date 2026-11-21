W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; K=$W/w24z12/out/kit_n_go; T=/scratch/jjyeung/orch_n30/n_review/r1f/tcpx; N=/scratch/jjyeung/orch_n30/n_review
date -u +%TZ
echo "== tree writers"; grep -rn --include=*.py 'population.json\|reader_filters\|"indices.json\|first_batch' $T < /dev/null 2>/dev/null | grep -v '/tests/' | cut -c1-240 | head -40
echo "== kit writers"; grep -n 'population\|reader_filters\|first_batch\|f1.json\|c%d\|"c"\|census\|v.json\|identity.txt\|live/' $K/b/cs.py $K/b/sv.py $K/b/pl.py $K/b/rv.py $K/b/h.py $K/b/z.py < /dev/null 2>/dev/null | cut -c1-260 | head -90
echo "== sv.py"; wc -l $K/b/sv.py < /dev/null; sed -n 1,120p $K/b/sv.py < /dev/null | cut -c1-300
echo "== rv.py 240-300"; sed -n 240,300p $K/b/rv.py < /dev/null | cut -c1-300
echo "== taska.py"; wc -l $N/r1f/chk/taska.py < /dev/null; grep -n 'def \|population\|reader_filter\|(d)' $N/r1f/chk/taska.py < /dev/null | head -40
