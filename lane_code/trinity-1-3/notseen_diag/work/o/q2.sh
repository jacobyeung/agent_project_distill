export TZ=UTC
W=/project/community/jjyeung/okh7/e6fc152498; cd $W/p446
du -sh h1eval b tree/trace_format tree/student_pilot orchard_h10 items inputs rows 2>&1
find h1eval -type f -printf '%s %p\n' | head -80
grep -rn -e "not seen" -e "box unavailable" -e "unresolved" h1eval b/e2e_reader tree/trace_format --include=*.py | cut -c1-240 | head -80
ls -la items inputs inputs/* rows | head -40
