#!/bin/bash
# lane_code_sync.sh [--dry]: hourly sync of agent-written lane code to GitHub branch lane-code.
# Stages whitelisted source/records from /scratch/jjyeung/orch_n30/*/ on each lane node (InfiniBand tar
# stream into $S/stage/<node>/ on trinity-3-30), plus orch_n30 tools/ and briefs/, secret-scans them,
# copies clean files into $S/repo/lane_code/<node>/..., commits on lane-code, pushes to origin and to the
# /home repo as branch lane-code. Runs on trinity-3-30 only. --dry prints per-node counts and stops;
# --stage-only stages, scans and copies into the clone, then stops before git.
# A failed run writes one line to the log and one BLOCKER event; the next attempt is the next hourly run.
set -u
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30
S=/scratch/jjyeung/distill_sync
R=$S/repo
EV=$B/events/code_sync
FILTER=$B/tools/lane_code_filter.py
SCAN=$B/tools/lane_code_scan.py
REMOTE_NODES="trinity-1-3 trinity-1-18"
DRY=0; [ "${1:-}" = "--dry" ] && DRY=1
STAGE_ONLY=0; [ "${1:-}" = "--stage-only" ] && STAGE_ONLY=1
FAILS=""
ts() { date -u +%FT%TZ; }
log() { echo "$(ts) $*"; }
fail() { FAILS="$FAILS; $*"; log "FAIL $*"; }
[ "$(hostname -s)" = trinity-3-30 ] || { log "FAIL not on trinity-3-30"; exit 2; }
exec 8>"$S/.sync.lock"; flock -n 8 || { log "FAIL previous run still holds the lock"; exit 3; }
log "START dry=$DRY"

# Remote script: filter on the lane node, then tar stream over InfiniBand into stage on trinity-3-30.
gen_remote() {
  local node=$1
  echo 'set -u'
  echo "cd /scratch/jjyeung/orch_n30 2>/dev/null || { echo 'STATS $node files=0 bytes=0 (no orch_n30)'; exit 0; }"
  if [ $DRY = 1 ]; then
    echo "python3 - $node code_sync/meta > /dev/null <<'PYEOF'"
  else
    echo "python3 - $node code_sync/meta <<'PYEOF' | tar --null -cf - -T - | timeout 900 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-3-30.ib 'mkdir -p $S/stage/$node && tar xf - -C $S/stage/$node'"
  fi
  cat "$FILTER"
  echo 'PYEOF'
  echo 'rc=("${PIPESTATUS[@]}"); echo "PIPE ${rc[*]}"; for r in "${rc[@]}"; do [ "$r" = 0 ] || exit 4; done'
}

for node in $REMOTE_NODES; do
  out=$(gen_remote "$node" | bash "$B/tools/tssh.sh" "$node" 'bash -s' 2>&1); rc=$?
  echo "$out" | sed "s/^/  [$node] /"
  [ $rc = 0 ] || fail "$node stage rc=$rc: $(echo "$out" | tail -1 | cut -c1-150)"
done

# Local node and orchestrator tools/briefs.
stage_local() {  # <src dir> <stage subdir> <label> [manifest dir]
  local src=$1 dst=$S/stage/$2 m=${4:-}
  ( cd "$src" || exit 5
    if [ $DRY = 1 ]; then python3 "$FILTER" "$3" $m > /dev/null; exit $?; fi
    mkdir -p "$dst" && python3 "$FILTER" "$3" $m | tar --null -cf - -T - | tar xf - -C "$dst"
    rc=("${PIPESTATUS[@]}"); for r in "${rc[@]}"; do [ "$r" = 0 ] || exit 4; done ) 2>&1
}
stage_local /scratch/jjyeung/orch_n30 trinity-3-30 trinity-3-30 code_sync/meta || fail "trinity-3-30 local stage"
stage_local "$B/tools" orch_n30/tools orch_n30/tools || fail "orch_n30 tools stage"
stage_local "$B/briefs" orch_n30/briefs orch_n30/briefs || fail "orch_n30 briefs stage"
[ $DRY = 1 ] && { log "DRY done${FAILS}"; exit 0; }

# Secret scan + copy clean files into the clone.
STAMP=$(date -u +%Y%m%dT%H%MZ)
python3 "$SCAN" "$S/stage" "$R/lane_code" "$S/flagged/flagged_$STAMP.txt" || fail "scan/copy rc=$?"
mkdir -p "$R/tools"
cp "$B/tools/lane_code_sync.sh" "$FILTER" "$SCAN" "$R/tools/" || fail "copy tools into clone"
[ $STAGE_ONLY = 1 ] && { log "STAGE-ONLY done${FAILS}"; exit 0; }

git -C "$R" add -f -A lane_code tools/lane_code_sync.sh tools/lane_code_filter.py tools/lane_code_scan.py || fail "git add"
if git -C "$R" diff --cached --quiet; then
  log "no changes"
else
  N=$(git -C "$R" diff --cached --name-only | wc -l)
  M=$(git -C "$R" diff --cached --name-only | awk -F/ '$1=="lane_code"{print $2"/"$3}' | sort -u | wc -l)
  git -C "$R" commit -q -m "lane-code sync $(date -u +%FT%H:%MZ): $N files, $M lanes changed" || fail "git commit"
  log "committed $N files, $M lanes: $(git -C "$R" rev-parse --short HEAD)"
fi
timeout 300 git -C "$R" push -q origin lane-code 2>&1 || fail "push origin lane-code"
timeout 300 git -C "$R" push -q home lane-code:lane-code 2>&1 || fail "push home lane-code"
H=$(git -C "$R" rev-parse HEAD)
G=$(timeout 60 git -C "$R" ls-remote origin refs/heads/lane-code 2>/dev/null | cut -f1)
[ "$H" = "$G" ] && log "verified GitHub lane-code = $H" || fail "GitHub lane-code $G != local $H"

if [ -n "$FAILS" ]; then
  echo "$(ts) code_sync run failed${FAILS} (log $S/sync.log; next attempt next hour)" > "$EV/${STAMP}_BLOCKER_sync_failed.md"
  log "END with failures"; exit 1
fi
log "END ok"
