for p in 3565420 3565421 3658189; do echo "== $p wchan=$(cat /proc/$p/wchan 2>/dev/null) syscall=$(cut -d' ' -f1-3 /proc/$p/syscall 2>/dev/null) ppid=$(ps -o ppid= -p $p)"; done
ps -u jjyeung -o pid,ppid,etimes,stat,args --forest | grep -B3 -A3 "code_sync/meta" | grep -v "grep" | cut -c1-160 | head -40
for q in 1154319664 1155924218; do echo "-- holders of pipe $q:"; for d in /proc/[0-9]*; do ls -l $d/fd 2>/dev/null | grep -q "pipe:\[$q\]" && echo "${d#/proc/} $(ps -o args= -p ${d#/proc/} | cut -c1-120)"; done; done
