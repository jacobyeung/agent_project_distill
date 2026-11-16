set -u
W=/scratch/jjyeung/orch_n30/k1_ops3/work/partb
B7=$W/build7
P=/scratch/jjyeung/envs/p1cpu/bin/python
date -u +%FT%TZ
for V in d3000 d600; do
  N=$W/build7_$V
  if [ -e $N ]; then echo "$N exists"; continue; fi
  mkdir -p $N/evidence/b7_tmp $N/out $N/inputs
  cd $B7
  for f in *; do case "$f" in evidence|rh|out|out_r1|jt|inputs) ;; *) cp -rp "$f" "$N/" ;; esac; done
  for f in inputs/*; do case "$f" in inputs/anchors.tar) ;; *) cp -p "$f" "$N/inputs/" ;; esac; done
  cd $N
  if [ $V = d600 ]; then
    $P -B -c "
from pathlib import Path; import os
p=Path('build_package.py'); assert os.stat(p).st_nlink==1; t=p.read_text(); a='capture_reserve_seconds=3000'; assert t.count(a)==1; p.write_text(t.replace(a,'capture_reserve_seconds=600')); print('reserve 600')"
  fi
  nice -n 19 $P -B build_package.py --deadline-unix 1794850800 > evidence/B7V_BUILD.log 2>&1; echo "$V build_rc=$?"; cat evidence/B7V_BUILD.log
  $P -B payload_diff.py $B7/packet/a7e31d84.sh packet/a7e31d84.sh > evidence/B7V_PAYLOAD_DIFF.json; cat evidence/B7V_PAYLOAD_DIFF.json | tr -d '\n' | cut -c1-400; echo
  $P -B -c "
import json; a=json.load(open('$B7/packet/CONFIG.json')); b=json.load(open('packet/CONFIG.json'))
print('config_changes', {k:(a.get(k),b.get(k)) for k in set(a)|set(b) if a.get(k)!=b.get(k)})"
  sha256sum packet/a7e31d84.sh packet/CONFIG.json
  sed "s#^N=.*#N=$N#" $B7/rh7.sh | sed '/--namespace/,$d' > rh7v.sh; echo 'date -u +%FT%TZ > evidence/B7_RH_END.txt' >> rh7v.sh
done
cd $W
cat > rh7v_both.sh <<'EOS'
#!/bin/bash
for V in d3000 d600; do bash /scratch/jjyeung/orch_n30/k1_ops3/work/partb/build7_$V/rh7v.sh; done
EOS
tmux new-session -d -s k1b7v "bash $W/rh7v_both.sh" && echo TMUX_STARTED; date -u +%FT%TZ
