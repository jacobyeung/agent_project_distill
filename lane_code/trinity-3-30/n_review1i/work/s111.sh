K=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w26fix/n_go; J=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z15/work/build24m4z15/j.sh
date -u +%TZ
grep -n "def bootstrap" -A 40 $K/b/z.py < /dev/null | cut -c1-230 | head -60
echo "== Q_KIT in decoded j.sh (discovery)"; grep -n "Q_KIT=\|Q_KIT \|/kit\b\|cp -a\|copytree" $J < /dev/null | cut -c1-200 | head -15
echo "== kit copies in z.py"; grep -n "'kit'\|\"kit\"\|copytree\|/'kit'\|copy2\|seal(" $K/b/z.py < /dev/null | cut -c1-200 | head -20
