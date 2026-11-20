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
printf '%s %s\n' "$TK_COPY_PID" "$TK_LOG_PID" > "$N/copier_pids"
sleep 0.2
exit 7
