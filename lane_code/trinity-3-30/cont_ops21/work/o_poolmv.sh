set -u; cd /project/community/jjyeung/okh7/ae71c903
while read h f; do n=${f%%/*}; o=$(sha256sum $f | cut -d' ' -f1); if [ "$o" = "$h" ] && [ ! -e ../ae71c903_fetched/$n ]; then mv $n ../ae71c903_fetched/$n && echo "moved $n"; else echo "skip $n $o"; fi; done
du -sb /project/community/jjyeung/okh7/ae71c903
