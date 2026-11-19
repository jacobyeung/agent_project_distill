cd /project/community/jjyeung/okh7
for P in a15_cot_ap*; do [ -d $P ] || continue; e=0; l=0; ino=""; if [ -e $P/a/e/0 ]; then e=$(du -sb --apparent-size $P/a/e | cut -f1); l=$(stat -c %h $P/a/e/0); ino=$(stat -c %i $P/a/e/0); fi
 printf '%s %s e=%s links=%s ino=%s job=%s f=%s mtime=%s\n' $P $(du -sb --apparent-size $P | cut -f1) $e $l "$ino" "$(cat $P/a/8.txt 2>/dev/null)" "$(test -e $P/a/f/EXIT.json && echo y || echo n)" "$(stat -c %y $P | cut -c1-16)"; done
echo TOTAL_UNIQUE $(du -sb a15_cot_ap* | tail -1); du -sbc a15_cot_ap* | tail -1
