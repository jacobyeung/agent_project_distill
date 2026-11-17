P=/project/community/jjyeung; W=$P/okh7/e6fc152498
grep -l -i "vnice\|terminator" $P/okh7/i_1be16f28/jb.sh $P/okh7/i_bb09a77d/b5/jb.sh $P/okh7/i_1be16f28/e/b/* 2>/dev/null | head
grep -h -o -i ".\{60\}terminator.\{60\}" $P/okh7/i_1be16f28/jb.sh $P/okh7/i_bb09a77d/b5/jb.sh 2>/dev/null | head -5
cat > $W/t2.sh <<'EOS'
cd /project/community/jjyeung/okh7/e6fc152498
timeout 1200 find /project/community/jjyeung -maxdepth 8 \( -name 'terminator*' -o -name 'vnice*' \) -type f 2>/dev/null > term3.txt
xargs -a term3.txt -d '\n' sha256sum > term3.sha 2>/dev/null; echo done $(date -u +%T) >> term3.sha
EOS
nohup nice -n 19 ionice -c3 bash $W/t2.sh >/dev/null 2>&1 </dev/null & echo t2started
cat $W/b.done | tail -4
