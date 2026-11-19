from pathlib import Path
p=Path('work/round1/tools/lane_code_stage.sh')
s=p.read_text()
s=s.replace('  RUN=$S/stage-robust', '  LOGGER=$B/tools/lane_code_log.py\n  [ -f "$LOGGER" ] || { fail "missing bounded-log helper"; return 2; }\n  RUN=$S/stage-robust')
s=s.replace('''    LCS_COPY_TMP="$R/.lcs-copy.pending" setsid --wait timeout --kill-after="$LCS_KILL_SECONDS" "$LCS_COPY_SECONDS" \\
      python3 "$SCAN" "$slot/accepted" "$R/lane_code/$label" "$slot/copy.flags" \\
      >> "$slot/run.log" 2>&1 8>&-''','''    LCS_COPY_TMP="$R/.lcs-copy.pending" python3 -I -s -B "$LOGGER" "$slot/run.log" - 1 \\
      setsid --wait timeout --kill-after="$LCS_KILL_SECONDS" "$LCS_COPY_SECONDS" \\
      python3 "$SCAN" "$slot/accepted" "$R/lane_code/$label" "$slot/copy.flags" 8>&-''')
s=s.replace('''    flock -n "$slot/incoming.lock" setsid --wait timeout --kill-after="$LCS_KILL_SECONDS" "$LCS_COPY_SECONDS" \\
      python3 "$SCAN" --accept-archive "$slot/incoming" "$slot/accepted" >> "$slot/run.log" 2>&1 8>&-''','''    python3 -I -s -B "$LOGGER" "$slot/run.log" - 1 flock -n "$slot/incoming.lock" \\
      setsid --wait timeout --kill-after="$LCS_KILL_SECONDS" "$LCS_COPY_SECONDS" \\
      python3 "$SCAN" --accept-archive "$slot/incoming" "$slot/accepted" 8>&-''')
s=s.replace('''    LCS_STAGE_TIMEOUT_OWNER=1 setsid --wait timeout --kill-after="$LCS_KILL_SECONDS" "$LCS_NODE_SECONDS" \\
      bash "$B/tools/tssh.sh" "$node" "$command" \\
      < "$slot/program.sh" > "$slot/run.log" 2>&1 8>&-''','''    LCS_STAGE_TIMEOUT_OWNER=1 python3 -I -s -B "$LOGGER" "$slot/run.log" "$slot/program.sh" 0 \\
      setsid --wait timeout --kill-after="$LCS_KILL_SECONDS" "$LCS_NODE_SECONDS" \\
      bash "$B/tools/tssh.sh" "$node" "$command" 8>&-''')
s=s.replace('''    setsid --wait timeout --kill-after="$LCS_KILL_SECONDS" "$LCS_REMOTE_SECONDS" bash "$slot/program.sh" \\
      > "$slot/run.log" 2>&1 8>&-''','''    python3 -I -s -B "$LOGGER" "$slot/run.log" - 0 \\
      setsid --wait timeout --kill-after="$LCS_KILL_SECONDS" "$LCS_REMOTE_SECONDS" bash "$slot/program.sh" 8>&-''')
p.write_text(s)
p=Path('work/round1/tools/lane_code_sync.sh')
s=p.read_text().replace('cp "$B/tools/lane_code_stage.sh" "$R/tools/"', 'cp "$B/tools/lane_code_stage.sh" "$B/tools/lane_code_log.py" "$R/tools/"').replace('git -C "$R" add -f tools/lane_code_stage.sh', 'git -C "$R" add -f tools/lane_code_stage.sh tools/lane_code_log.py')
p.write_text(s)
p=Path('work/round1/tests/support.py')
s=p.read_text().replace("for name in ('lane_code_sync.sh', 'lane_code_filter.py', 'lane_code_stage.sh', 'lane_code_scan.py'):", "for name in ('lane_code_sync.sh', 'lane_code_filter.py', 'lane_code_stage.sh', 'lane_code_scan.py', 'lane_code_log.py'):\n            if not (TOOLS / name).exists():\n                continue")
p.write_text(s)
p=Path('work/round1/install_tools.py')
s=p.read_text().replace("        helper = base / 'tools' / 'lane_code_stage.sh'\n        if helper.exists() or helper.is_symlink():\n            raise ValueError('new helper already exists; reconcile before installation')", "        for name in ('lane_code_stage.sh', 'lane_code_log.py'):\n            helper = base / 'tools' / name\n            if helper.exists() or helper.is_symlink():\n                raise ValueError('new helper already exists; reconcile before installation: ' + name)")
s=s.replace("names = ['lane_code_filter.py', 'lane_code_scan.py', 'tssh.sh', 'lane_code_stage.sh', 'lane_code_sync.sh']", "names = ['lane_code_log.py', 'lane_code_filter.py', 'lane_code_scan.py', 'tssh.sh', 'lane_code_stage.sh', 'lane_code_sync.sh']")
p.write_text(s)
p=Path('work/round1/build_patches.py')
s=p.read_text().replace("names+['lane_code_stage.sh']", "names+['lane_code_stage.sh','lane_code_log.py']").replace("'tools/lane_code_stage.sh','tests/support.py'", "'tools/lane_code_stage.sh','tools/lane_code_log.py','tests/test_log.py','tests/support.py'").replace('all six postimage tools','all seven postimage tools')
p.write_text(s)
