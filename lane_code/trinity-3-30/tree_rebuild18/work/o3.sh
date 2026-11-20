export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"
grep -v "archive members verified\|staged$" $X/j/a15_cot_ap24d9b8e2_173567.log | tail -4 | cut -c1-300
ls -la $X/o/173567/ $X/o/173567/live 2>/dev/null | head -40; tail -5 $X/o/173567/q.steps | cut -c1-250; tail -c 1500 $X/o/173567/q.log
echo "== n resolve"; ls $X/n/b | grep -i resol; grep -n "add_argument" $X/n/b/resolve.py | cut -c1-200; diff -q $X/n/b/resolve.py $X/qd/b/resolve.py
