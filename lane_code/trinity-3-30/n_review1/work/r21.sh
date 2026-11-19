W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; M=/scratch/jjyeung/orch_n30/n_review
cd $M/tree
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'P'
import sys,json; sys.path.insert(0,'.')
from student_pilot.r1_handover import pin_values
from student_pilot.p3_provenance import digest
r=json.load(open('/scratch/jjyeung/orch_n30/n_review/x/u/8957d119bfa6776efe776816675da6d0f610a6e8c336acd66c297f29cf4e7e0f'))
print('pose stream identity', digest(pin_values(r)))
for h in ['ca0616dbc67cf9a257774b43a9d5b134957b3f3ce0451e6bf5378f3d7d0c1984','93b21a3aeeda01efab90d9f818eff78a6ca182c18c964534279008e4af91733a','e3ee51daa46af30fa8e84a05c12448d7fc3dc9cade05284707f9df322bbe44d0']:
    print(h[:8], json.load(open('/scratch/jjyeung/orch_n30/n_review/x/u/'+h))['database']['sha256'])
P
grep -n "^SHA256\|def __init__\|pinned\|path" student_pilot/r2_withheld.py | head -15
f=/scratch/jjyeung/devs1c_models/cp1/base/config.json; sha256sum $f; grep -o '"tie_word_embeddings": *[a-z]*' $f
for h in 3119aa4a9594e4507372b99243afc8210fe217393466ac4e5ae78485e7c83970 a1869ae28f6d3f1815993da776f4c4798f67bad4c555c3bb80cc48fcecb23af5; do f=$(ls $W/work/up24/u/$h $W/w24/work/*/upload*/u/$h 2>/dev/null | head -1); echo "== $h $f"; head -c 600 $(readlink -f $f); echo; done
