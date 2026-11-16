OLD=/project/community/jjyeung/vla_libero; T=/project/community/jjyeung/45e92888780e_w; mkdir -p $T; cd $OLD || exit 1
echo "== my /tmp"; find /tmp -maxdepth 1 -user jjyeung 2>/dev/null | head; df -h /tmp | tail -1
echo "== procs"; ps -u jjyeung -o pid,args | grep -F "$OLD" | grep -v grep | cut -c1-150
echo "== text files with OLD (targeted)"
{ ls envs/*/pyvenv.cfg; find envs/*/bin -maxdepth 1 -type f; find envs -path '*site-packages*' -maxdepth 5 \( -name '*.pth' -o -name '*.egg-link' -o -name '__editable__*' -o -name 'direct_url.json' \); find cfg st -type f; find kit -type f -not -path '*/__pycache__/*'; find osmesa/lib/pkgconfig osmesa/bin -maxdepth 1 -type f 2>/dev/null; find py -maxdepth 6 \( -name '_sysconfigdata*.py' -o -name '*.pc' -o -name 'Makefile' \) 2>/dev/null; find py -maxdepth 3 -path '*/bin/*' -type f 2>/dev/null; } 2>/dev/null | sort -u > $T/reloc_cands.txt
wc -l < $T/reloc_cands.txt
xargs -d '\n' grep -lI -F "$OLD" < $T/reloc_cands.txt 2>/dev/null > $T/reloc_hits.txt; wc -l < $T/reloc_hits.txt; cut -d/ -f1-3 $T/reloc_hits.txt | sort | uniq -c | sort -rn | head -20
echo "== py dir"; ls py; cat st/p310_path; ls -la envs/e_sv/bin/python* envs/e_lb/bin/python*; cat envs/e_sv/pyvenv.cfg
echo "== src egg/dist-info with OLD"; nice -n 19 grep -rlI -F "$OLD" src --include='*.txt' --include='*.cfg' --include='*.json' --include='*.pth' 2>/dev/null | head
echo "== binary (non-text) bin files with OLD"; find envs/*/bin -maxdepth 1 -type f | xargs grep -l -F "$OLD" 2>/dev/null | xargs -r grep -LI -F "$OLD" | head
echo "== parent"; ls -la /project/community/jjyeung | head -5; df -h /project/community | tail -1
