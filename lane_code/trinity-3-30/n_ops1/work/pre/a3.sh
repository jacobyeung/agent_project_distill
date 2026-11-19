export TZ=UTC; date -u +%FT%TZ; X=/project/community/jjyeung/okh7/x_22c714e1
sacct -j 172660,173236,173222 -X -P -o JobID,JobName%24,Partition,Timelimit,AllocTRES%80,ReqMem,Submit,Start,End,State,NodeList
for f in t.py u.py g.py o.py w.py s.py m.py d.py a.py e.sh f.sh q.sh q1.sh v.py resolve.py; do echo "==== b/$f"; cat $X/n/b/$f; echo; done
for f in a.json r.json h.json 8.json g.json; do echo "==== k/$f"; head -c 1500 $X/n/k/$f; echo; done
echo "==== z.py"; base64 -w0 < <(gzip -c $X/n/b/z.py); echo
