export TZ=UTC; date -u +%TZ
R=/project/community/jjyeung/okh7/x_ee227714/runs/6ed2c7aa
ls -la $R | head -60
for d in $(ls -d $R/checkpoint_* 2>/dev/null | head -3); do echo "== $d"; ls -la --time-style=+%FT%T $d $d/shards 2>&1 | head -40; done
for d in $(ls -d $R/m* 2>/dev/null | head -1); do echo "== $d"; ls -la $d | head -30; done
ls -d $R/_superseded/* 2>/dev/null | head
echo "== sacct 174246"; sacct -j 174246 -X -n -P -o JobID,ReqMem,AllocCPUS,NodeList,AllocTRES%80
echo "== nodes"; for n in orchard-community-2 orchard-community-3; do scontrol show node $n | grep -oE "CPUAlloc=[0-9]+|CPUTot=[0-9]+|CPULoad=[0-9.]+|RealMemory=[0-9]+|AllocMem=[0-9]+|FreeMem=[0-9]+|State=[A-Z+_]+" | tr '\n' ' '; echo " $n"; done
squeue -w orchard-community-2,orchard-community-3 -h -o '%i|%u|%P|%T|%C|%m' | head
ls -la /project/community/jjyeung/c7d31ddd/venvs/rwtrain_torch211_cu129/bin/python*
