date -u +%TZ
F=/tmp/fix9_find.txt
echo "== packed/route/u.gz candidates (unique name+size)"; grep -E "_packed.jsonl.gz|ROUTE_DIRECT|/u.gz$" $F | awk '{n=$2; sub(".*/","",n); k=n" "$1; if(!(k in s)){s[k]=$2; print $1, $2}}' > /tmp/fix9_c1.txt; wc -l < /tmp/fix9_c1.txt
echo "== routing or pose sqlite candidates"; grep -E "routing/rows.sqlite|a2v3|a3v2|pose|/d.db$" $F | awk '$1>10000000' > /tmp/fix9_c2.txt; wc -l < /tmp/fix9_c2.txt; awk '{print $1}' /tmp/fix9_c2.txt | sort | uniq -c | sort -k2n | head -40
WANT="b32359ce256a 0b95850a2dec 4e8e6c04e697 a67a3f6f4890 1169024c0739 75c8f3436382 8807075c0473 2331a5bbb181 b37de067725d cbff008bb2ab 0298d22ae6a8 42c520ec4f5b 2f2fd779179a 947cbb9fa7d6 086c857c721c 92927870a7b4 14439f0c658d"
echo "== sha of packed candidates"
while read sz p; do s=$(nice -n 10 sha256sum "$p" | cut -c1-12); case " $WANT " in *" $s "*) echo "HIT $s $sz $p";; esac; done < /tmp/fix9_c1.txt
echo "== sha of sqlite candidates (one per size)"
awk '!(($1) in s){s[$1]=1; print}' /tmp/fix9_c2.txt | while read sz p; do s=$(nice -n 10 sha256sum "$p" | cut -c1-12); case " $WANT " in *" $s "*) echo "HIT $s $sz $p";; *) echo "no $s $sz $p";; esac; done
date -u +%TZ
