W=/project/community/jjyeung/okh7/e6fc152498; cd $W
cat h.done m.sha g.sha 2>/dev/null
which vnice vnice.sh terminator.sh 2>/dev/null; ls /usr/local/bin 2>/dev/null | grep -i -E "nice|term" 
cat > t.sh <<'EOS'
cd /project/community/jjyeung/okh7/e6fc152498
{ timeout 300 find /home/jjyeung -maxdepth 8 -name 'terminator*' -type f 2>/dev/null
  timeout 300 find /project/community -maxdepth 4 -name 'terminator*.sh' -type f 2>/dev/null
  timeout 60 find /opt /usr/local -maxdepth 4 -name 'terminator*' -type f 2>/dev/null; } > term2.txt
xargs -a term2.txt -d '\n' sha256sum > term2.sha 2>/dev/null; echo done $(date -u +%T) >> term2.sha
EOS
nohup nice -n 19 ionice -c3 bash t.sh >/dev/null 2>&1 </dev/null & echo tstarted
