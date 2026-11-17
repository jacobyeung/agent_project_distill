cd /tmp; A=/home/jjyeung/okit/i/eb3429c5/eb3429c5.tar
tar -tf $A | tail -4; tar -tf $A | sort | uniq -d
tar -xOf $A SHA256SUMS | wc -l
tar -xOf $A SHA256SUMS | grep -v -E '^[0-9a-f]{64} [ *].+$' | cat -A | head
tar -xOf $A SHA256SUMS | awk '{print $2}' | sort | uniq -d
