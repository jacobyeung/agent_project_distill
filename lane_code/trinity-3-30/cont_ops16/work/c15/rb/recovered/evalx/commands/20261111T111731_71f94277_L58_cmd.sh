<!-- recovered by seal_plan: transcript=71f94277 line=58 utc=2026-11-11T11:17:31.894Z kind=commands original_path=(bash command)  -->
echo "== me: $$ ppid $PPID"; ps -o pid,ppid,lstart,etime,stat,args -p $PPID 2>/dev/null | cut -c1-200
echo "== sessions"; ps -o pid,ppid,lstart,etime,stat,args -p 1245144,3240727 2>/dev/null | cut -c1-220
echo "== lanes"; ps -o pid,etime,stat,args -p 1005742,3212143,652190,677553 2>/dev/null | cut -c1-200
echo "== paused"; ps -o pid,etime,stat,args -p 713837,1161730,1161728,999696,1128272,3539044,3546734,3832334 2>/dev/null | cut -c1-160
echo "== watchers"; pgrep -u jjyeung -af 'evwait.sh|lanewatch.sh|queue_watcher.sh' | cut -c1-220
echo "== my scratchpad"; ls -la /tmp/claude-25409/-scratch-jjyeung-orch-home-distill/71f94277-362e-467c-a4bc-ccc9ae6b87c8/scratchpad 2>&1 | head
echo "== old scratchpads"; ls -d /tmp/claude-25409/-scratch-jjyeung-orch-home-distill/*/scratchpad 2>/dev/null
for l in evalx orchard_cp2 label_247 gemini_native mdg_next; do echo "== $l"; ls -t /scratch/jjyeung/orch_cd/$l/events 2>/dev/null | head -3; done