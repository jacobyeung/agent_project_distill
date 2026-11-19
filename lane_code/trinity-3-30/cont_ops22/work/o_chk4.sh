P=/project/community/jjyeung/okh7/a15_cot_apdd982cd5c4b25; cat $P/3.py; echo; cat $P/SUBMIT.cmd; echo; ls -la $P; ps -u jjyeung -o pid,etime,cmd | cut -c1-150 | grep -v 'ps -u' | head
