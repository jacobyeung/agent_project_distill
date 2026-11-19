cd /project/community/jjyeung/okh7
for t in da6f7936c1779 d296bd1ef61cd dc863c3e6b41d d7a6db629db02 dacd91c2f5c4b fadf2291c654b dd92e95963089; do P=a15_cot_ap$t; printf '%s ' $P; du -sb --apparent-size $P 2>/dev/null | cut -f1 | tr '\n' ' '; du -sb $P/a/e 2>/dev/null | cut -f1 | tr '\n' ' '; stat -c '%h' $P/a/e/0 2>/dev/null | sed 's/^/links=/' | tr '\n' ' '; stat -c '%y' $P/a/e/0 2>/dev/null | cut -c1-16; done
du -sb ae71c903 813f42db/c20d400rcode a15_cot_ap7e4d49a0f823 2>/dev/null
df -BG /project/community | tail -1; date -u +%TZ
