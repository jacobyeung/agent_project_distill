for p in 3565420 3565421 3658189 $(pgrep -f "python3 - trinity-1-18 code_sync/meta"); do
  echo "== pid $p: $(ps -o etimes=,stat=,wchan:20=,args= -p $p 2>/dev/null | cut -c1-150)"
  ls -l /proc/$p/fd 2>/dev/null | awk '{print $9,$10,$11}' | grep -v "^ *$" | head -12
  cat /proc/$p/stack 2>/dev/null | head -3
done
