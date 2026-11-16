<!-- recovered by seal_plan: transcript=a97ad692 line=1946 utc=2026-11-15T06:54:44.909Z kind=commands original_path=(bash command)  -->
R=/scratch/jjyeung/orch_cd; P=$R/evalx/work/milestone/native_package_s24_05; J=$P/PILOT9_REVIEW_READY.json; wc -c $J; for k in 4d05c37b294797877128c13c32e64ca6a19ac9b148a444f6936c432a069ccef8 3688e98758d834254fa3066f76687321ee42e91f7f8535b4460004746c8d70af ebe307cf4 1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef 079f876a; do echo "$k: $(grep -c "$k" $J)"; done; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "
import json
d=json.load(open('$J'))
print(list(d.keys())[:30])
for k in ('mode','partition','step','token','family_sha256','artifact','packet','status','verdict'):
    if k in d: print(k, str(d[k])[:160])
"; ls $P | grep -i 'packet\|PILOT9' | head -8