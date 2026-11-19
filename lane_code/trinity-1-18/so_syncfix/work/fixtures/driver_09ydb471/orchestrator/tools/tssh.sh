N=$1; shift
exec timeout 900 ssh -o ConnectTimeout=20 -o BatchMode=yes "$N" "$@"
