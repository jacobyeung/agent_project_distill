TZ=UTC sacct -j 173701 -X -n -o JobID,State,Elapsed,NodeList%22,ExitCode
ls -la /project/community/jjyeung/ae63d9b7124fc/ | awk '{print $5, $9}' | tr '\n' ' '; echo
tail -c 300 /project/community/jjyeung/ae63d9b7124fc/5.stderr 2>/dev/null
