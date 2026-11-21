tail -c 1500 /tmp/aa3b73b53d92a73.yfeWqGHF.log; echo; ls -la /project/community/jjyeung/a3b73b53d92a7/a/f 2>&1
TZ=UTC sacct -j 174135,174200 -X -n -o JobID,State,Start,Elapsed,NodeList%30 | tr -s ' '
