date -u +%TZ
A=""; for w in b32359ce 0b95850a 4e8e6c04 a67a3f6f 1169024c 75c8f343 8807075c 2331a5bb b37de067 cbff008b 0298d22a 42c520ec 2f2fd779 947cbb9f 086c857c 92927870 14439f0c a1869ae2 3119aa4a; do A="$A -o -name ${w}*"; done
timeout 400 nice -n 10 find /scratch -xdev \( -false $A \) -size +1k -printf '%s %p\n' 2>/dev/null | sort -k2 | awk '{n=$2; sub(".*/","",n); k=substr(n,1,8); c[k]++; if(c[k]<=3) print}'
echo rc=$?
date -u +%TZ
