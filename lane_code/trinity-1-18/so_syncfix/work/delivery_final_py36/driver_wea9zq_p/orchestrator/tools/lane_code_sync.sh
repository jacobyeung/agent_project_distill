#!/bin/bash
# lane_code_sync.sh [--dry]: hourly sync of agent-written lane code to GitHub branch lane-code.
# Stages whitelisted source/records from /scratch/jjyeung/orch_n30/so_syncfix/work/delivery_final_py36/driver_wea9zq_p/sources/trinity-3-30/*/ on each lane node (InfiniBand tar
# stream into legacy directories or robust tar slots on trinity-3-30), plus tools/ and briefs/, secret-scans them,
# copies clean files into $S/repo/lane_code/<node>/..., commits on lane-code, pushes to origin and to the
# /home repo as branch lane-code. Runs on trinity-3-30 only. --dry prints per-node counts and stops;
# --stage-only stages, scans and copies into the clone, then stops before git.
# A failed run writes one line to the log and one BLOCKER event; the next attempt is the next hourly run.
set -u
# --queue-only runs only the push-queue step (publish queued eff/* branches; see push_queue below).
# Robust mode is OFF unless LCS_ROBUST_SYNC=1 or the regular, non-symlink file
# $S/LCS_ROBUST_SYNC exists. The running hourly tmux loop checks it every invocation.
# Robust budgets may be set in $S/LCS_ROBUST_BUDGETS; environment values take precedence.
# Other LCS_* path overrides support local tests.
B=${LCS_B:-/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30}
S=${LCS_S:-/scratch/jjyeung/distill_sync}
if [ "${LCS_ROBUST_SYNC:-0}" = 1 ] || { [ -f "$S/LCS_ROBUST_SYNC" ] && [ ! -L "$S/LCS_ROBUST_SYNC" ]; }; then
  export LCS_ROBUST_SYNC=1
fi
R=${LCS_R:-$S/repo}
EV=${LCS_EV:-$B/events/code_sync}
FILTER=$B/tools/lane_code_filter.py
SCAN=${LCS_SCAN:-$B/tools/lane_code_scan.py}
LANES_ROOT=${LCS_LANES_ROOT:-/scratch/jjyeung/orch_n30/so_syncfix/work/delivery_final_py36/driver_wea9zq_p/sources/trinity-3-30}
REMOTE_NODES="trinity-1-18"  # trinity-1-3 fenced 2026-11-18 (unreachable since 11:29Z); add it back when it answers
DRY=0; [ "${1:-}" = "--dry" ] && DRY=1
STAGE_ONLY=0; [ "${1:-}" = "--stage-only" ] && STAGE_ONLY=1
QUEUE_ONLY=0; [ "${1:-}" = "--queue-only" ] && QUEUE_ONLY=1
FAILS=""
ts() { date -u +%FT%TZ; }
log() { echo "$(ts) $*"; }
fail() { FAILS="$FAILS; $*"; log "FAIL $*"; }
[ "$(hostname -s)" = trinity-3-30 ] || { log "FAIL not on trinity-3-30"; exit 2; }
exec 8>"$S/.sync.lock"; flock -n 8 || { log "FAIL previous run still holds the lock"; exit 3; }
log "START dry=$DRY queue_only=$QUEUE_ONLY"

# Push-queue step: publish each builder branch queued in <lane>/PUSH_QUEUE.txt to origin.
# A queue line is "<UTC> <branch> <sha> [<clone path>]". Accepted only: branch ^eff/[a-z0-9-]+$, a lane folder
# $LANES_ROOT/(e|eff)_<name>, a clone at <lane>/clone or <lane>/repo (a link between those two is fine), the fetched branch head equal to or
# descending from <sha>, and no secret-scan flag on the files the branch changes against main. The push is
# "origin <sha>:refs/heads/<branch>" without force, verified with ls-remote. Done lines go to $S/PUSH_DONE.txt,
# permanent refusals (logged once) to $S/PUSH_REFUSED.txt; a transient fetch or push failure retries next hour.
# The step never checks out a branch, never writes main and never touches /home.
QBLOCK=""
qlog() { log "QUEUE $*"; }
qrefuse() { echo "$(ts) $1 $2 $3 REFUSED $4" >> "$S/PUSH_REFUSED.txt"; qlog "REFUSED $2 $3 ($1): $4"; }
qblock() { qrefuse "$@"; QBLOCK="$QBLOCK
- $2 $3 from $1: $4"; }
qseen() { awk -v l="$1" -v b="$2" -v s="$3" '$2==l && $3==b && $4==s {f=1} END {exit !f}' \
            "$S/PUSH_DONE.txt" "$S/PUSH_REFUSED.txt"; }
push_queue() {
  local q lane name utc br sha cpath extra clone head mainref base dir flag rem out rc n=0 qstamp
  qstamp=$(date -u +%Y%m%dT%H%M%SZ)
  touch "$S/PUSH_DONE.txt" "$S/PUSH_REFUSED.txt"
  if git -C "$R" rev-parse -q --verify refs/remotes/origin/main >/dev/null; then mainref=refs/remotes/origin/main
  else mainref=refs/heads/main; fi
  for q in "$LANES_ROOT"/e_*/PUSH_QUEUE.txt "$LANES_ROOT"/eff_*/PUSH_QUEUE.txt; do
    [ -f "$q" ] || continue
    lane=${q%/PUSH_QUEUE.txt}; name=${lane##*/}
    while read -r utc br sha cpath extra <&3; do
      [ -n "${utc:-}" ] || continue
      case "$utc" in \#*) continue ;; esac
      qseen "$lane" "${br:-}" "${sha:-}" && continue
      n=$((n+1))
      if ! [[ "${br:-}" =~ ^eff/[a-z0-9-]+$ ]]; then qrefuse "$lane" "${br:-?}" "${sha:-?}" "branch is not eff/<slug>"; continue; fi
      if ! [[ "${sha:-}" =~ ^[0-9a-f]{40}$ ]]; then qrefuse "$lane" "$br" "${sha:-?}" "sha is not 40 hex"; continue; fi
      if ! [[ "$name" =~ ^(e|eff)_[a-z0-9_-]+$ ]] || [ -n "${extra:-}" ]; then qrefuse "$lane" "$br" "$sha" "lane folder or line outside the pattern"; continue; fi
      [ -n "${cpath:-}" ] || { cpath=$lane/clone; [ -d "$cpath" ] || cpath=$lane/repo; }
      clone=$(realpath -e "$cpath" 2>/dev/null)
      if { [ "$cpath" != "$lane/clone" ] && [ "$cpath" != "$lane/repo" ]; } \
         || { [ "$clone" != "$lane/clone" ] && [ "$clone" != "$lane/repo" ]; } \
         || [ "$(realpath -e "$lane" 2>/dev/null)" != "$lane" ] || [ ! -d "$clone/.git" ]; then
        qrefuse "$lane" "$br" "$sha" "clone path $cpath is not <lane>/clone or <lane>/repo"; continue; fi
      if ! timeout 300 git -C "$R" fetch -q --no-tags "$clone" "refs/heads/$br" 2>&1; then
        fail "queue fetch $br from $clone"; continue; fi
      head=$(git -C "$R" rev-parse FETCH_HEAD)
      if [ "$head" != "$sha" ] && ! git -C "$R" merge-base --is-ancestor "$sha" "$head" 2>/dev/null; then
        qblock "$lane" "$br" "$sha" "branch head $head neither equals nor descends from the queued sha"; continue; fi
      base=$(git -C "$R" merge-base "$sha" "$mainref" 2>/dev/null) || base=$(git -C "$R" hash-object -t tree /dev/null)
      dir=$S/qscan/${qstamp}_$n; flag=$S/flagged/queue_${qstamp}_$n.txt
      mkdir -p "$dir" "$S/flagged"
      out=$(git -C "$R" diff --name-only -z --no-renames --diff-filter=d "$base" "$sha" | while IFS= read -r -d '' p; do
              mkdir -p "$dir/$(dirname "$p")" && git -C "$R" cat-file blob "$sha:$p" > "$dir/$p" || echo "unreadable $p"; done)
      if [ -n "$out" ]; then qblock "$lane" "$br" "$sha" "scan could not read: $(echo "$out" | head -3 | tr '\n' ' ')"; continue; fi
      python3 "$SCAN" "$dir" "$dir" "$flag" | sed 's/^/  [queue] /'
      if [ ! -f "$flag" ] || [ -s "$flag" ]; then
        qblock "$lane" "$br" "$sha" "secret scan flagged: $(cut -f1 "$flag" 2>/dev/null | head -5 | tr '\n' ' ')(list $flag)"; continue; fi
      out=$(timeout 300 git -C "$R" push -q origin "$sha:refs/heads/$br" 2>&1 < /dev/null); rc=$?
      rem=$(timeout 60 git -C "$R" ls-remote origin "refs/heads/$br" 2>/dev/null | cut -f1)
      if [ $rc = 0 ] && [ "$rem" = "$sha" ]; then
        echo "$(ts) $lane $br $sha pushed" >> "$S/PUSH_DONE.txt"; qlog "pushed $br $sha from $name"
      elif [ -n "$rem" ] && [ "$rem" != "$sha" ] && git -C "$R" merge-base --is-ancestor "$sha" "$rem" 2>/dev/null; then
        echo "$(ts) $lane $br $sha superseded_by $rem" >> "$S/PUSH_DONE.txt"; qlog "superseded $br $sha (origin has $rem)"
      elif [ -n "$rem" ] && [ "$rem" != "$sha" ] && ! git -C "$R" merge-base --is-ancestor "$rem" "$sha" 2>/dev/null; then
        qblock "$lane" "$br" "$sha" "non-fast-forward: origin has $rem; not forced"
      else
        fail "queue push $br $sha rc=$rc remote=${rem:-none}: $(echo "$out" | tail -1 | cut -c1-150)"
      fi
    done 3< "$q"
  done
  qlog "done: $n new lines"
  if [ -n "$QBLOCK" ]; then
    { echo "$(ts) code_sync push queue blocked these lines (log $S/sync.log; refusals in $S/PUSH_REFUSED.txt):"
      echo "$QBLOCK"; echo "Fix the branch, commit, and queue the new head; a blocked line is never retried."; } \
      > "$EV/${qstamp}_BLOCKER_push_queue.md"
  fi
}
if [ $QUEUE_ONLY = 1 ]; then
  push_queue
  [ -n "$FAILS" ] && { log "QUEUE-ONLY END with failures${FAILS}"; exit 1; }
  log "QUEUE-ONLY END ok"; exit 0
fi

STAGE_ROOT=$S/stage
robust_early_exit() {
  # Do not fall back to the unbounded path after the owner enabled robust mode.
  STAMP=$(date -u +%Y%m%dT%H%MZ)
  echo "$(ts) code_sync run failed${FAILS} (log $S/sync.log; next attempt next hour)" > "$EV/${STAMP}_BLOCKER_sync_failed.md"
  log "END with failures"; exit 2
}
if [ "${LCS_ROBUST_SYNC:-0}" = 1 ]; then
  # Keep the legacy path unchanged unless the coordinator explicitly enables this.
  if ! . "$B/tools/lane_code_stage.sh"; then fail "load robust staging"; robust_early_exit; fi
  robust_stages || { fail "initialize robust staging"; robust_early_exit; }
else
# Remote script: filter on the lane node, then tar stream over InfiniBand into stage on trinity-3-30.
gen_remote() {
  local node=$1
  echo 'set -u'
  echo "cd /scratch/jjyeung/orch_n30/so_syncfix/work/delivery_final_py36/driver_wea9zq_p/sources/trinity-3-30 2>/dev/null || { echo 'STATS $node files=0 bytes=0 (no orch_n30)'; exit 0; }"
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
stage_local /scratch/jjyeung/orch_n30/so_syncfix/work/delivery_final_py36/driver_wea9zq_p/sources/trinity-3-30 trinity-3-30 trinity-3-30 code_sync/meta || fail "trinity-3-30 local stage"
stage_local "$B/tools" orch_n30/tools orch_n30/tools || fail "orch_n30 tools stage"
stage_local "$B/briefs" orch_n30/briefs orch_n30/briefs || fail "orch_n30 briefs stage"
fi
[ $DRY = 1 ] && { log "DRY done${FAILS}"; exit 0; }

# Secret scan + copy clean files into the clone.
STAMP=$(date -u +%Y%m%dT%H%MZ)
if [ "${LCS_ROBUST_SYNC:-0}" = 1 ]; then
  robust_copy
else
  python3 "$SCAN" "$STAGE_ROOT" "$R/lane_code" "$S/flagged/flagged_$STAMP.txt" || fail "scan/copy rc=$?"
fi
mkdir -p "$R/tools"
cp "$B/tools/lane_code_sync.sh" "$FILTER" "$SCAN" "$R/tools/" || fail "copy tools into clone"
if [ "${LCS_ROBUST_SYNC:-0}" = 1 ]; then
  cp "$B/tools/lane_code_stage.sh" "$B/tools/lane_code_log.py" "$R/tools/" || fail "copy robust helper into clone"
fi
[ $STAGE_ONLY = 1 ] && { log "STAGE-ONLY done${FAILS}"; exit 0; }

git -C "$R" add -f -A lane_code tools/lane_code_sync.sh tools/lane_code_filter.py tools/lane_code_scan.py || fail "git add"
if [ "${LCS_ROBUST_SYNC:-0}" = 1 ]; then
  git -C "$R" add -f tools/lane_code_stage.sh tools/lane_code_log.py || fail "git add robust helper"
fi
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

push_queue

if [ -n "$FAILS" ]; then
  echo "$(ts) code_sync run failed${FAILS} (log $S/sync.log; next attempt next hour)" > "$EV/${STAMP}_BLOCKER_sync_failed.md"
  log "END with failures"; exit 1
fi
log "END ok"
