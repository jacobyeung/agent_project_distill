L=/tmp/aa3b73b53d92a72.E9Hs3xam.log; tail -c 400 $L; echo
J=$(cat /project/community/jjyeung/a3b73b53d92a7/a/8.txt 2>/dev/null); echo "job=$J"
[ -n "$J" ] && { echo "$(date -u +%T) $(TZ=UTC sacct -j $J -X -n -o State,Start,Elapsed,ExitCode,NodeList%40 | tr -s ' ')"; }
