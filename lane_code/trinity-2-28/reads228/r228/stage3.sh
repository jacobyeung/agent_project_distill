#!/bin/bash
# swarm_opt4: governed Orchard pulls of the 13 runtime parts (MISSING.json of so_reads228 round 1) into trinity-2-28; plus bwrap and d/s facts
set -u
R=/scratch/jjyeung/orch_n30/reads228; K=$R/r228; D=$R/dl; L=$R/lists; B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30
date -u +%FT%TZ; mkdir -p $L
{ command -v bwrap; bwrap --version; ls -l $(command -v bwrap); } > $L/bwrap.txt 2>&1; cat $L/bwrap.txt
ls -la /scratch/jjyeung/b01ec87a6f29b/d/s/ > $L/d_s.txt 2>&1; find /scratch/jjyeung/b01ec87a6f29b/d/s -type f -printf '%s %p\n' 2>/dev/null | sort -k2 > $L/d_s_files.txt; wc -l $L/d_s_files.txt
CP='/tmp/cm-n30-orchard-%r'
if ! ssh -o ControlPath=$CP -O check orchard 2>/dev/null; then setsid nohup ssh -fN -o ControlMaster=yes -o ControlPath=$CP -o ControlPersist=3h -o ServerAliveInterval=30 -o ConnectTimeout=60 -o BatchMode=yes orchard </dev/null >$D/master3.log 2>&1; sleep 5; fi
ssh -o ControlPath=$CP -O check orchard 2>&1 || { echo NO_MASTER; exit 4; }
timeout 120 bash $B/tools/ossh.sh "ls -l /home/jjyeung/okit/p/d59945c1/ /project/community/jjyeung/bd8ae51c/p/d59945c1/" </dev/null > $D/orchard_ls_r.txt 2>&1; grep -c . $D/orchard_ls_r.txt
ok=1; while read -r n p b s; do grep -q " $b .*${p##*/}\$" $D/orchard_ls_r.txt || { echo "MISSING_OR_SIZE $n $p $b"; ok=0; }; done < $K/PINS_R.txt
(( ok )) || { echo ABORT_NO_LAUNCH; exit 5; }
cd $K
while read -r n p b s; do [[ -e $D/$n ]] && { echo "EXISTS $n skip"; continue; }
  setsid nohup /usr/bin/python3 -s gov_stream2.py --lane swarm_opt_r228_$n --expected-bytes $b --reader "[\"bash\",\"$B/tools/ossh.sh\",\"cat $p\"]" --out $D/$n --io-weight 1 --kind pull --priority 100 > $D/$n.log 2>&1 < /dev/null &
  sleep 2; done < $K/PINS_R.txt
sleep 8; for n in $(cut -d' ' -f1 $K/PINS_R.txt); do echo "$n: $(tail -1 $D/$n.log)"; done
