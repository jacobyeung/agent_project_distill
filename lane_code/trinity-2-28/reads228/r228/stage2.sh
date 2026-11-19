#!/bin/bash
# swarm_opt4: diagnose the dropped s4e0 pull, then one new governed stream s4e0b (ORCH default 17:20Z of BLOCKER 1654Z)
set -u
R=/scratch/jjyeung/orch_n30/reads228; K=$R/r228; D=$R/dl; B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30
date -u +%FT%TZ; echo "== s4e0.log (last 30)"; tail -30 $D/s4e0.log | cut -c1-300; ls -l --time-style=+%FT%T $D/s4e0; for n in s4e1 s4e2 s4e3 g0 a2.tar a4.tar a3.tar; do echo "$n $(stat -c %s $D/$n) $(tail -1 $D/$n.log 2>/dev/null) $(ls $D/$n.sha_ok 2>/dev/null)"; done
echo "== ssh processes"; pgrep -af "ssh.*orchard" | cut -c1-200
CP='/tmp/cm-n30-orchard-%r'; ssh -o ControlPath=$CP -O check orchard 2>&1
MP=$(ssh -o ControlPath=$CP -O check orchard 2>&1 | sed -n 's/.*pid=\([0-9]*\).*/\1/p'); [ -n "$MP" ] || { echo "NO_EXISTING_MASTER: inconclusive, no redo"; exit 0; }; ST=$(ps -o lstart= -p $MP); SE=$(date -d "$ST" +%s); echo "master pid $MP started $(date -u -d @$SE +%FT%TZ)"
T0=$(date -d 2026-11-19T15:51:53Z +%s); [ "$SE" -gt "$T0" ] && echo "MASTER_STARTED_AFTER_DROP" || { echo "MASTER_OLDER_THAN_DROP: no redo"; exit 0; }
[ "${1:-}" = "--go" ] || { echo "diagnose only"; exit 0; }
if ! ssh -o ControlPath=$CP -O check orchard 2>/dev/null; then setsid nohup timeout 120 ssh -fN -o ControlMaster=yes -o ControlPath=$CP -o ControlPersist=2h -o ServerAliveInterval=30 -o ConnectTimeout=60 -o BatchMode=yes orchard </dev/null >$D/master2.log 2>&1; sleep 3; ssh -o ControlPath=$CP -O check orchard 2>&1 || { echo NO_MASTER; exit 4; }; fi
cd $K; read -r n p b s < $K/PINS2.txt; [ -e $D/$n ] && { echo "EXISTS $n"; exit 5; }
setsid nohup /usr/bin/python3 -s gov_stream2.py --lane swarm_opt_r228_$n --expected-bytes $b --reader "[\"bash\",\"$B/tools/ossh.sh\",\"cat $p\"]" --out $D/$n --io-weight 1 --kind pull --priority 9 > $D/$n.log 2>&1 < /dev/null &
sleep 8; tail -2 $D/$n.log
