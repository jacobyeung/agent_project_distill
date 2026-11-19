#!/bin/bash
# swarm_opt4: governed Orchard pulls of the A4 reader inputs into trinity-2-28 /scratch (one stream per file, registered together)
set -u
P=/project/community/jjyeung/okh7/a15_cot_apdc76460c3a164/a/e; R=/scratch/jjyeung/orch_n30/reads228; K=$R/r228; D=$R/dl; mkdir -p $D
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; G=/data3/jjyeung/orch_n13_20261026/io_governor
hostname -s; date -u +%FT%TZ; df -h /scratch | tail -1; free -g | sed -n 2p; uptime
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader
if [ ! -f /scratch/jjyeung/io_governor/ratelimit.py ]; then mkdir -p /scratch/jjyeung/io_governor && cd /scratch/jjyeung/io_governor && rsync --bwlimit=8000 $G/helpers_rehome-v1-ratelimit.tgz . && tar xzf helpers_rehome-v1-ratelimit.tgz && echo HELPERS_INSTALLED; fi
ls /scratch/jjyeung/io_governor/ | tr '\n' ' '; echo
if ! tmux has-session -t iogov_agent 2>/dev/null; then mkdir -p /scratch/jjyeung/io_governor_serial && cd /scratch/jjyeung/io_governor_serial && rsync --bwlimit=8000 $G/serial_governor_v1.tgz . && tar xzf serial_governor_v1.tgz && bash code/start_agent.sh; sleep 5; fi
tmux has-session -t iogov_agent 2>/dev/null && echo AGENT_OK || { echo AGENT_MISSING; exit 3; }
CP='/tmp/cm-n30-orchard-%r'
if ! ssh -o ControlPath=$CP -O check orchard 2>/dev/null; then timeout 120 ssh -fN -o ControlMaster=yes -o ControlPath=$CP -o ControlPersist=6h -o ConnectTimeout=60 -o BatchMode=yes orchard </dev/null >/dev/null 2>&1; fi
ssh -o ControlPath=$CP -O check orchard 2>&1 || { echo NO_ORCHARD_MASTER; exit 4; }
timeout 120 bash $B/tools/ossh.sh "ls -l /project/community/jjyeung/okh7/a15_cot_apdc76460c3a164/a/e/ /project/community/jjyeung/okh7/e6fc152498/g/ /project/community/jjyeung/okh7/e6fc152498/a2.tar /project/community/jjyeung/okh7/e6fc152498/a4.tar /project/community/jjyeung/okh7/e6fc152498/a3.tar" </dev/null > $D/orchard_ls.txt 2>&1; cat $D/orchard_ls.txt
ok=1; while read -r n p b s; do grep -q " $b .*${p##*/}\$" $D/orchard_ls.txt || { echo "MISSING_OR_SIZE $n $p $b"; ok=0; }; done < $K/PINS.txt
(( ok )) || { echo ABORT_NO_LAUNCH; exit 5; }
cd $K
timeout 120 bash $B/tools/ossh.sh "cat /project/community/jjyeung/okh7/e6fc152498/a3.tar" </dev/null > $D/a3.tar; sha256sum $D/a3.tar
while read -r n p b s; do [[ $n == a3.tar ]] && continue; [[ -e $D/$n ]] && { echo "EXISTS $n skip"; continue; }
  setsid nohup /usr/bin/python3 -s gov_stream2.py --lane swarm_opt_r228_${n%.tar} --expected-bytes $b --reader "[\"bash\",\"$B/tools/ossh.sh\",\"cat $p\"]" --out $D/$n --io-weight 1 --kind pull --priority 100 > $D/$n.log 2>&1 < /dev/null &
  sleep 2; done < $K/PINS.txt
sleep 8; for f in $D/*.log; do echo "$f: $(tail -2 $f | tr '\n' ' ')"; done; ls /data3/jjyeung/orch_n13_20261026/io_governor/streams/ | grep r228
