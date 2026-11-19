for p in 3565420 3565421 3658189; do echo "$p: $(ps -o etimes=,args= -p $p | cut -c1-80)"; done
kill 3565420 3565421 3658189 2>&1; sleep 3
for p in 3565420 3565421 3658189 3658190; do ps -p $p >/dev/null && echo "$p still alive" || echo "$p gone"; done
cd /scratch/jjyeung/orch_n30 && timeout 240 nice -n 10 find . -xdev \( -name .git -o -name __pycache__ -o -name site-packages -o -name node_modules -o -name envs \) -prune -o -type p -print 2>/dev/null | head -20; echo "find rc=$?"
