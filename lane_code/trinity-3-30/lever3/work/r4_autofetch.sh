#!/bin/bash
# Plain-script fetch + score for rank 4's GPU read (no agent needed). Run in tmux l3_r4auto on trinity-3-30.
# Polls job 173990 every 120 s through ossh; on a terminal state: production fetch (3.py fetch R g), bring R/0.tgz back,
# place it as 2-28 r4kit/out/return.tgz, run score.py there, save call_rates.json here, post an event (RESULT >=95%, QUESTION <95%, BLOCKER on no return).
set -u
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; EV=$B/events/lever
J=173990; P=/project/community/jjyeung/okh7/a15_cot_ap87f4ae5c2f44f; R=/project/community/jjyeung/okh7/af87f4ae5c2f44f
O=/scratch/jjyeung/orch_n30/lever3/out/r4_gpu_173990; LOG=$O/auto.log; mkdir -p $O
log(){ echo "$(date -u +%FT%TZ) $*" >> $LOG; }
ev(){ local kind=$1 slug=$2 body=$3; local S=$(date -u +%Y%m%dT%H%MZ); printf '%s\n' "$body" > $EV/${S}_${kind}_${slug}.md; log "event ${S}_${kind}_${slug}"; }
fails=0; started=""
while true; do
  st=$(timeout 300 bash $B/tools/ossh.sh "TZ=UTC sacct -j $J -X -n -o State,Elapsed,ExitCode,Start,End | tr -s ' '" 2>>$LOG)
  if [ -z "$st" ]; then fails=$((fails+1)); log "poll failed ($fails)"; [ $fails -ge 2 ] && { ev BLOCKER rank4_autofetch_orchard_poll_failed_twice "# BLOCKER (lever3 r4_autofetch): two Orchard polls of job $J failed; script stopped. Log: $LOG"; exit 2; }; sleep 120; continue; fi
  fails=0; log "$st"; state=$(echo $st | awk '{print $1}')
  case "$state" in PENDING|RUNNING|REQUEUED|CONFIGURING|COMPLETING|SUSPENDED) [ "$state" = RUNNING ] && [ -z "$started" ] && { started=1; log "job started"; }; sleep 120; continue;; esac
  break
done
log "terminal: $st"
timeout 300 bash $B/tools/ossh.sh "/usr/bin/python3 -I -s -B $P/3.py fetch $R g > /dev/null 2>/tmp/af87f4ae5c2f44f_fetch.err; echo rc=\$? >&2; tail -c 1500 /tmp/af87f4ae5c2f44f_fetch.err >&2; cat $R/0.tgz" > $O/return.tgz 2>>$LOG
sz=$(stat -c %s $O/return.tgz 2>/dev/null || echo 0); sha=$(sha256sum $O/return.tgz | cut -c1-64); log "return bytes=$sz sha=$sha"
if [ "$sz" -lt 100 ]; then ev BLOCKER rank4_gpu_read_${J}_no_return "# BLOCKER (lever3 r4_autofetch): rank 4 GPU read $J ended ($st) and the production fetch returned no archive ($sz B). Nothing resubmitted. Log: $LOG (trinity-3-30)."; exit 3; fi
/usr/bin/python3 - $O/return.tgz > $O/decoded_diag.txt 2>&1 <<'PY'
import json,sys,tarfile
with tarfile.open(sys.argv[1]) as a:
    print(a.getnames())
    for n in ('1.json','2.json','4.json','3.jsonl'):
        if n not in a.getnames(): continue
        for line in a.extractfile(n):
            line=line.strip()
            if line: print('=====',n); print(json.dumps(json.loads(bytes.fromhex(json.loads(line)['a0'])),indent=1)[:20000])
PY
timeout 600 bash $B/tools/tssh.sh trinity-2-28 "cd /scratch/jjyeung/orch_n30/lever1_c/r4kit && (set -C; cat > out/return.tgz) && sha256sum out/return.tgz >&2 && nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B score.py out/return.tgz --out out/call_rates.json >/dev/null 2>out/score.err; echo score_rc=\$? >&2; tail -c 1500 out/score.err >&2; cat out/call_rates.json" < $O/return.tgz > $O/call_rates.json 2>>$LOG
log "score done: $(head -c 300 $O/call_rates.json | tr '\n' ' ')"
summary=$(/usr/bin/python3 - $O/call_rates.json <<'PY'
import json,sys
try: r=json.load(open(sys.argv[1]))
except Exception as e: print('SCOREFAIL',e); sys.exit()
if not r.get('complete'): print('INCOMPLETE',json.dumps(r)[:600]); sys.exit()
f=lambda k:f"{100*r[k]['rate']:.1f}% [{100*r[k]['ci95'][0]:.1f}, {100*r[k]['ci95'][1]:.1f}]"
print('PASS' if r['REVSI']['rate']>=.95 else 'UNDER', f"ORIG {f('ORIG')}; REVSI {f('REVSI')}; REVSI-ORIG {f('REVSI_minus_ORIG')} (pp); pairs {r['pairs']}, rooms {r['rooms']}, {r['draws']} paired room draws, seed {r['seed']}; gate: {r['gate']}; other calls {json.dumps(r.get('other_calls'))[:300]}")
PY
)
verdict=${summary%% *}; rest=${summary#* }
body="# rank 4 (WORD) GPU read $J: $verdict (lever3 r4_autofetch, plain script)
- Job: $st. Return $sz B sha $sha; production fetch + score.py on trinity-2-28 lever1_c/r4kit/out/{return.tgz,call_rates.json}; copies trinity-3-30 $O/.
- Call rate (ground call opened within 64 tokens, step-400 init export 5083243c, 290 R0-dev pairs): $rest
- Registered reading: REVSI >= 95% -> no change; under 95% -> arm D builds rows for that family (arm D stays closed until the orchestrator rules).
- Diagnostics decode: $O/decoded_diag.txt."
case "$verdict" in
  PASS) ev RESULT rank4_word_gpu_read_${J}_revsi_call_rate_at_or_above_95 "$body";;
  UNDER) ev QUESTION rank4_word_gpu_read_${J}_revsi_call_rate_under_95_arm_D "$body
Default: arm D stays closed; the orchestrator decides.";;
  *) ev RESULT rank4_word_gpu_read_${J}_returned_without_a_verdict "$body
The read returned but scoring gave no verdict ($verdict); a death that returns its cause may be fixed and resubmitted once after this RESULT.";;
esac
log "done"
