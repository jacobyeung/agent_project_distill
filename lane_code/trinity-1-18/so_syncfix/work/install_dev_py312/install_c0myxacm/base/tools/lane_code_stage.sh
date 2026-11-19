#!/bin/bash
# Sourced only in robust mode (environment switch or $S/LCS_ROBUST_SYNC file).
# Each source reuses incoming/accepted tar slots; only complete archives reach SCAN.
robust_config() {
  export LCS_ROBUST_SYNC=1
  # A regular configuration file lets the owner calibrate the existing tmux loop.
  # Only numeric assignments to the listed budget names are accepted; never source it.
  local v value extra maximum
  if [ -f "$S/LCS_ROBUST_BUDGETS" ] && [ ! -L "$S/LCS_ROBUST_BUDGETS" ]; then
    while IFS='=' read -r v value extra; do
      [ -n "$v" ] || continue
      case "$v" in
        LCS_FILE_SECONDS|LCS_SCAN_SECONDS|LCS_COPY_SECONDS|LCS_LEG_SECONDS|LCS_REMOTE_SECONDS|LCS_NODE_SECONDS|LCS_KILL_SECONDS) ;;
        *) fail "invalid budget name $v"; return 2 ;;
      esac
      [ -z "$extra" ] && [[ "$value" =~ ^[0-9]+([.][0-9]+)?$ ]] || {
        fail "invalid budget assignment $v"; return 2;
      }
      [ -n "${!v:-}" ] || printf -v "$v" '%s' "$value"
    done < "$S/LCS_ROBUST_BUDGETS"
  fi
  LCS_FILE_SECONDS=${LCS_FILE_SECONDS:-3}
  LCS_SCAN_SECONDS=${LCS_SCAN_SECONDS:-120}
  LCS_COPY_SECONDS=${LCS_COPY_SECONDS:-120}
  LCS_LEG_SECONDS=${LCS_LEG_SECONDS:-150}
  LCS_REMOTE_SECONDS=${LCS_REMOTE_SECONDS:-160}
  LCS_NODE_SECONDS=${LCS_NODE_SECONDS:-210}
  LCS_KILL_SECONDS=${LCS_KILL_SECONDS:-5}
  export LCS_FILE_SECONDS LCS_NODE_SECONDS LCS_KILL_SECONDS
  for v in LCS_FILE_SECONDS LCS_SCAN_SECONDS LCS_COPY_SECONDS LCS_LEG_SECONDS LCS_REMOTE_SECONDS LCS_NODE_SECONDS LCS_KILL_SECONDS; do
    maximum=3600; [ "$v" != LCS_FILE_SECONDS ] || maximum=30
    [[ ${!v} =~ ^[0-9]+([.][0-9]+)?$ ]] &&
      awk -v n="${!v}" -v maximum="$maximum" 'BEGIN {exit !(n > 0 && n <= maximum)}' || {
        fail "invalid $v=${!v}"; return 2;
      }
  done
  RUN=$S/stage-robust
  mkdir -p "$RUN" || return 2
  ACCEPTED_LABELS=''
  log "ROBUST slots=$RUN file_seconds=$LCS_FILE_SECONDS scan_seconds=$LCS_SCAN_SECONDS copy_seconds=$LCS_COPY_SECONDS leg_seconds=$LCS_LEG_SECONDS remote_seconds=$LCS_REMOTE_SECONDS node_seconds=$LCS_NODE_SECONDS kill_seconds=$LCS_KILL_SECONDS"
}

robust_snapshot() {  # Read a finite regular-file snapshot; retain one capped log per label.
  local slot=$1 snapshot
  snapshot=$(head -c 65535 "$slot/run.log")
  printf '%s\n' "$snapshot" > "$slot/run.log"
  printf '%s\n' "$snapshot"
}

robust_copy() {
  local label slot rc flags=$S/flagged/flagged_robust.txt
  mkdir -p "$S/flagged" || { fail "create flags directory"; return 0; }
  printf '' > "$flags"
  # This list belongs to this invocation; a preserved accepted slot is never enough.
  for label in $ACCEPTED_LABELS; do
    slot=$RUN/$label
    printf '' > "$slot/copy.flags"
    log "ROBUST copy $label"
    LCS_COPY_TMP="$R/.lcs-copy.pending" setsid --wait timeout --kill-after="$LCS_KILL_SECONDS" "$LCS_COPY_SECONDS" \
      python3 "$SCAN" "$slot/accepted" "$R/lane_code/$label" "$slot/copy.flags" \
      >> "$slot/run.log" 2>&1 8>&-
    rc=$?
    robust_snapshot "$slot" | sed "s|^|  [copy $label] |"
    sed "s|^|$label/|" "$slot/copy.flags" >> "$flags"
    [ "$rc" = 0 ] || fail "$label scan/copy rc=$rc (log $slot/run.log)"
    log "COPIED $label rc=$rc"
  done
}

robust_program() {  # <source> <label> <manifest> <slot> <remote:0|1>
  local source=$1 label=$2 manifest=$3 slot=$4 remote=$5 receiver writer
  echo 'set -u'
  printf 'cd %q 2>/dev/null || { echo %q; exit 66; }\n' "$source" "SKIP $label no orch_n30/source"
  if [ "$DRY" = 1 ]; then
    printf 'timeout --kill-after=%q %q env LCS_ROBUST_SYNC=1 LCS_FILE_SECONDS=%q python3 - %q %q > /dev/null' \
      "$LCS_KILL_SECONDS" "$LCS_SCAN_SECONDS" "$LCS_FILE_SECONDS" "$label" "$manifest"
    echo " <<'LCS_FILTER_EOF'"
  else
    printf 'timeout --kill-after=%q %q env LCS_ROBUST_SYNC=1 LCS_FILE_SECONDS=%q python3 - %q %q' \
      "$LCS_KILL_SECONDS" "$LCS_SCAN_SECONDS" "$LCS_FILE_SECONDS" "$label" "$manifest"
    printf " <<'LCS_FILTER_EOF' | timeout --kill-after=%q %q tar --null -cf - -T - | " \
      "$LCS_KILL_SECONDS" "$LCS_LEG_SECONDS"
    # A receiver surviving a disconnected client retains this lock; another attempt
    # cannot overwrite its incoming archive until it exits. No per-run copies.
    printf -v writer 'cat > %q' "$slot/incoming"
    printf -v receiver 'flock -n %q timeout --kill-after=%q %q bash -c %q' \
      "$slot/incoming.lock" "$LCS_KILL_SECONDS" "$LCS_LEG_SECONDS" "$writer"
    if [ "$remote" = 1 ]; then
      printf 'timeout --kill-after=%q %q ssh -o ConnectTimeout=20 -o ConnectionAttempts=1 -o BatchMode=yes trinity-3-30.ib %q\n' \
        "$LCS_KILL_SECONDS" "$LCS_LEG_SECONDS" "$receiver"
    else
      printf '%s\n' "$receiver"
    fi
  fi
  cat "$FILTER" || return 2
  echo 'LCS_FILTER_EOF'
  echo 'rc=("${PIPESTATUS[@]}"); echo "PIPE ${rc[*]}"; for r in "${rc[@]}"; do [ "$r" = 0 ] || exit 4; done'
}

robust_finish() {  # <label> <status>
  local label=$1 rc=$2 slot=$RUN/$1 expected='PIPE 0 0 0' snapshot
  [ "$DRY" = 1 ] && expected='PIPE 0'
  snapshot=$(robust_snapshot "$slot")
  printf '%s\n' "$snapshot" | sed "s|^|  [$label] |"
  if [ "$rc" = 66 ] && grep -Fxq "SKIP $label no orch_n30/source" <<< "$snapshot"; then
    log "SKIP $label (no source root)"; return 0
  fi
  if [ "$label" = trinity-2-28 ] && { [ "$rc" = 255 ] || [ "$rc" = 124 ] || [ "$rc" = 137 ]; } &&
      ! grep -Eq '^(STATS|PIPE) ' <<< "$snapshot"; then
    log "SKIP $label (unreachable or silent; rc=$rc)"; return 0
  fi
  if [ "$rc" != 0 ] || ! grep -Fxq "$expected" <<< "$snapshot"; then
    fail "$label stage rc=$rc (not published: archive may contain changed or incomplete files; log $slot/run.log)"
    return 0
  fi
  if [ "$DRY" != 1 ]; then
    log "ROBUST accept $label"
    flock -n "$slot/incoming.lock" setsid --wait timeout --kill-after="$LCS_KILL_SECONDS" "$LCS_COPY_SECONDS" \
      python3 "$SCAN" --accept-archive "$slot/incoming" "$slot/accepted" >> "$slot/run.log" 2>&1 8>&-
    rc=$?
    if [ "$rc" != 0 ]; then
      robust_snapshot "$slot" | sed "s|^|  [$label] |"
      fail "$label accept stage rc=$rc (log $slot/run.log)"; return 0
    fi
    ACCEPTED_LABELS="$ACCEPTED_LABELS $label"
  fi
  log "STAGED $label rc=0"
}

robust_slot() {
  local slot=$RUN/$1
  mkdir -p "$slot" || return 2
  # Keep stable names and overwrite metadata; do not retain per-invocation files.
  printf '' > "$slot/run.log" && printf '' > "$slot/copy.flags"
}

robust_stages() {
  robust_config || return $?
  local node rc command source label manifest slot
  REMOTE_NODES=${LCS_REMOTE_NODES:-"trinity-1-18 trinity-2-28"}
  for node in $REMOTE_NODES; do
    case "$node" in trinity-[0-9]-[0-9]|trinity-[0-9]-[0-9][0-9]) ;;
      *) fail "invalid remote node $node"; continue ;; esac
    slot=$RUN/$node
    robust_slot "$node" || { fail "$node mkdir/log"; continue; }
    log "ROBUST stage $node"
    robust_program "$LANES_ROOT" "$node" code_sync/meta "$slot" 1 > "$slot/program.sh" || {
      fail "$node generate script"; continue;
    }
    printf -v command 'timeout --kill-after=%q %q bash -s' "$LCS_KILL_SECONDS" "$LCS_REMOTE_SECONDS"
    # SSH receives regular descriptors, and cannot inherit the driver's lock.
    LCS_STAGE_TIMEOUT_OWNER=1 setsid --wait timeout --kill-after="$LCS_KILL_SECONDS" "$LCS_NODE_SECONDS" \
      bash "$B/tools/tssh.sh" "$node" "$command" \
      < "$slot/program.sh" > "$slot/run.log" 2>&1 8>&-
    rc=$?
    robust_finish "$node" "$rc"
  done
  for label in trinity-3-30 orch_n30/tools orch_n30/briefs; do
    case "$label" in
      trinity-3-30) source=$LANES_ROOT; manifest=code_sync/meta ;;
      orch_n30/tools) source=$B/tools; manifest='' ;;
      orch_n30/briefs) source=$B/briefs; manifest='' ;;
    esac
    slot=$RUN/$label
    robust_slot "$label" || { fail "$label mkdir/log"; continue; }
    log "ROBUST stage $label"
    robust_program "$source" "$label" "$manifest" "$slot" 0 > "$slot/program.sh" || {
      fail "$label generate script"; continue;
    }
    setsid --wait timeout --kill-after="$LCS_KILL_SECONDS" "$LCS_REMOTE_SECONDS" bash "$slot/program.sh" \
      > "$slot/run.log" 2>&1 8>&-
    rc=$?
    robust_finish "$label" "$rc"
  done
}
