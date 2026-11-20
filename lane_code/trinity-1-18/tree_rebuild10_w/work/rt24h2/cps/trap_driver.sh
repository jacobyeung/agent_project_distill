set -eu
umask 077
ROOT="$TEST_KIT"
N="$TEST_ROOT"
export ROOT N
exec 9>"$N/shell.xtrace"
BASH_XTRACEFD=9
PS4='+ pid=$BASHPID line=$LINENO '
set -x
source "$ROOT/b/pc.sh"
# These PIDs belong only to this disposable test.
printf '%s %s\n' "$TK_COPY_PID" "$TK_LOG_PID" > "$N/copier_pids"
sleep 0.2
case "$TEST_VARIANT" in
 EXIT) exit "$TEST_STATUS" ;;
 TERM) kill -TERM "$$" ;;
 USR1) kill -USR1 "$$" ;;
 TERM_BUSY)
   (sleep 440) &
   TK_WORK_PID=$!
   kill -TERM "$$" ;;
 TERM_WORKER|USR1_WORKER)
   (sleep 0.3; exit "$TEST_STATUS") &
   TK_WORK_PID=$!
   if [[ "$TEST_VARIANT" == TERM_WORKER ]]; then kill -TERM "$$"; else kill -USR1 "$$"; fi ;;
esac
exit 99
