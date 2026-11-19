#!/bin/bash
# r1_ops8: one-line summary of local monitor files; prints FLAG on any regression signal
M=/scratch/jjyeung/orch_n30/r1_ops6/work/mon; R=/scratch/jjyeung/orch_n30/r1_ops6/work/r7/m400
st=$(grep '^STEP' $M/node_last.txt | tail -1 | grep -o '"step": [0-9]*, "wall": [0-9]*' | tr -d '"')
ev=$(python3 -c "import json;d=json.load(open('$M/node_early.json'));print(d['verdict'],len(d['problems']))")
js=$(grep -E '^172660\|' $M/last.txt | head -1 | cut -d'|' -f4)
oe=$(awk '/^172660.err/{f=1;next} /^172660.steps/{f=0} f' $M/last.txt | grep -v -c -E '_cgroup_procs_check|unable to read .*cgroup.procs|^th /sys')
rcs=$(grep -E 'srun rc|early rc' $M/node_last.txt | tr '\n' ' ')
slow=$(grep -v '"step": 201' $M/node_last.txt | grep -o '"wall": [0-9]*' | awk '$2>300' | wc -l)
ck=$(grep -o 'checkpoint_[0-9]*' $M/node_last.txt | sort -u | tail -1)
fl=""; [[ $ev != "PASS 0" ]] && fl+=" EARLY"; [[ $js != RUNNING ]] && fl+=" STATE"; (( oe > 1 )) && fl+=" ERR"; (( slow > 0 )) && fl+=" SLOW"; [[ $rcs != *"srun rc=0"*"early rc=0"* ]] && fl+=" RC"; [[ -e $R/alarm ]] && fl+=" M400ALARM"
echo "$(date -u +%T) node@$(head -1 $M/node_last.txt|cut -c12-19) pool@$(head -1 $M/last.txt|cut -c12-19) $st early=$ev job=$js err+=$((oe-1)) $ck m400:[$(ls $R | tr '\n' ' ')] df=$(df -BG --output=avail /scratch|tail -1) ${fl:+FLAG$fl}"
