#!/bin/bash
# Sourced by lane_code_sync.sh only when LCS_ROBUST_SYNC=1.
# Each attempt writes an isolated directory; only complete stages reach SCAN.
robust_config() {
  export LCS_ROBUST_SYNC=1
  LCS_FILE_SECONDS=${LCS_FILE_SECONDS:-3}
  LCS_SCAN_SECONDS=${LCS_SCAN_SECONDS:-120}
  LCS_LEG_SECONDS=${LCS_LEG_SECONDS:-150}
  LCS_REMOTE_SECONDS=${LCS_REMOTE_SECONDS:-160}
  LCS_NODE_SECONDS=${LCS_NODE_SECONDS:-210}
  LCS_KILL_SECONDS=${LCS_KILL_SECONDS:-5}
  export LCS_FILE_SECONDS
  local v
  for v in LCS_FILE_SECONDS LCS_SCAN_SECONDS LCS_LEG_SECONDS LCS_REMOTE_SECONDS LCS_NODE_SECONDS LCS_KILL_SECONDS; do
    # A zero timeout disables GNU timeout. Do not accept it, shell text, or suffixes.
    [[ ${!v} =~ ^[0-9]+([.][0-9]+)?$ ]] &&
      awk -v n="${!v}" 'BEGIN {exit !(n > 0 && n <= 3600)}' || {
        fail "invalid $v=${!v}"; return 2;
      }
  done
  mkdir -p "$S/stage-runs" || return 2
  RUN=$(mktemp -d "$S/stage-runs/run.XXXXXXXX") || return 2
  STAGE_ROOT=$RUN/accepted
  mkdir -p "$RUN/incoming" "$STAGE_ROOT" || return 2
  log "ROBUST run=$RUN node_seconds=$LCS_NODE_SECONDS kill_seconds=$LCS_KILL_SECONDS"
}

robust_program() {  # <source> <label> <manifest> <destination> <remote:0|1>
  local source=$1 label=$2 manifest=$3 dest=$4 remote=$5 receiver
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
    if [ "$remote" = 1 ]; then
      printf -v receiver 'timeout --kill-after=%q %q tar xf - -C %q' \
        "$LCS_KILL_SECONDS" "$LCS_LEG_SECONDS" "$dest"
      printf 'timeout --kill-after=%q %q ssh -o ConnectTimeout=20 -o ConnectionAttempts=1 -o BatchMode=yes trinity-3-30.ib %q\n' \
        "$LCS_KILL_SECONDS" "$LCS_LEG_SECONDS" "$receiver"
    else
      printf 'timeout --kill-after=%q %q tar xf - -C %q\n' "$LCS_KILL_SECONDS" "$LCS_LEG_SECONDS" "$dest"
    fi
  fi
  cat "$FILTER" || return 2
  echo 'LCS_FILTER_EOF'
  echo 'rc=("${PIPESTATUS[@]}"); echo "PIPE ${rc[*]}"; for r in "${rc[@]}"; do [ "$r" = 0 ] || exit 4; done'
}

robust_finish() {  # <label> <key> <status>
  local label=$1 key=$2 rc=$3 expected='PIPE 0 0 0'
  [ "$DRY" = 1 ] && expected='PIPE 0'
  # A detached child may still own the log. Read a finite snapshot, never wait for EOF.
  head -c 65536 "$RUN/$key.log" > "$RUN/$key.snapshot"
  sed "s|^|  [$label] |" "$RUN/$key.snapshot"
  if [ "$rc" != 0 ] || ! grep -Fxq "$expected" "$RUN/$key.snapshot"; then
    fail "$label stage rc=$rc (skipped; previous stage and clone preserved; log $RUN/$key.log)"
    return 0
  fi
  if [ "$DRY" != 1 ]; then
    mkdir -p "$(dirname "$STAGE_ROOT/$label")" &&
      mv "$RUN/incoming/$key" "$STAGE_ROOT/$label" || {
        fail "$label accept stage"; return 0;
      }
  fi
  log "STAGED $label rc=0"
}

robust_stages() {
  robust_config || return $?
  local node key rc command source label manifest
  # The optional override is for local fake-SSH tests; production uses these two nodes.
  REMOTE_NODES=${LCS_REMOTE_NODES:-"trinity-1-18 trinity-2-28"}
  for node in $REMOTE_NODES; do
    case "$node" in trinity-[0-9]-[0-9]|trinity-[0-9]-[0-9][0-9]) ;;
      *) fail "invalid remote node $node"; continue ;; esac
    key=$node
    mkdir -p "$RUN/incoming/$key" || { fail "$node mkdir"; continue; }
    robust_program "$LANES_ROOT" "$node" code_sync/meta "$RUN/incoming/$key" 1 > "$RUN/$key.sh" || {
      fail "$node generate script"; continue;
    }
    printf -v command 'timeout --kill-after=%q %q bash -s' "$LCS_KILL_SECONDS" "$LCS_REMOTE_SECONDS"
    # setsid isolates timeout's process group. No output pipe reaches SSH descendants.
    # Close the driver's lock fd so a surviving master cannot lock out the next hour.
    setsid --wait timeout --kill-after="$LCS_KILL_SECONDS" "$LCS_NODE_SECONDS" \
      bash "$B/tools/tssh.sh" "$node" "$command" \
      < "$RUN/$key.sh" > "$RUN/$key.log" 2>&1 8>&-
    rc=$?
    robust_finish "$node" "$key" "$rc"
  done
  for key in local tools briefs; do
    case "$key" in
      local) source=$LANES_ROOT; label=trinity-3-30; manifest=code_sync/meta ;;
      tools) source=$B/tools; label=orch_n30/tools; manifest='' ;;
      briefs) source=$B/briefs; label=orch_n30/briefs; manifest='' ;;
    esac
    mkdir -p "$RUN/incoming/$key" || { fail "$label mkdir"; continue; }
    robust_program "$source" "$label" "$manifest" "$RUN/incoming/$key" 0 > "$RUN/$key.sh" || {
      fail "$label generate script"; continue;
    }
    setsid --wait timeout --kill-after="$LCS_KILL_SECONDS" "$LCS_REMOTE_SECONDS" bash "$RUN/$key.sh" \
      > "$RUN/$key.log" 2>&1 8>&-
    rc=$?
    robust_finish "$label" "$key" "$rc"
  done
}
