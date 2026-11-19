from pathlib import Path
p=Path('work/round1/tools/lane_code_sync.sh')
s=p.read_text().replace('# The LCS_* variables exist for tests only; production runs set none of them.', '''# Robust mode is OFF unless LCS_ROBUST_SYNC=1 or the regular, non-symlink file
# $S/LCS_ROBUST_SYNC exists. The running hourly tmux loop checks it every invocation.
# Robust budgets may be set in $S/LCS_ROBUST_BUDGETS; environment values take precedence.
# Other LCS_* path overrides support local tests.''')
s=s.replace('STAGE_ROOT=$S/stage\n', '''STAGE_ROOT=$S/stage
if [ "${LCS_ROBUST_SYNC:-0}" = 1 ] || { [ -f "$S/LCS_ROBUST_SYNC" ] && [ ! -L "$S/LCS_ROBUST_SYNC" ]; }; then
  export LCS_ROBUST_SYNC=1
fi
robust_early_exit() {
  # Do not fall back to the unbounded path after the owner enabled robust mode.
  STAMP=$(date -u +%Y%m%dT%H%MZ)
  echo "$(ts) code_sync run failed${FAILS} (log $S/sync.log; next attempt next hour)" > "$EV/${STAMP}_BLOCKER_sync_failed.md"
  log "END with failures"; exit 2
}
''',1)
s=s.replace('fail "load robust staging"; exit 2;', 'fail "load robust staging"; robust_early_exit;')
s=s.replace('fail "initialize robust staging"; exit 2;', 'fail "initialize robust staging"; robust_early_exit;')
p.write_text(s)
