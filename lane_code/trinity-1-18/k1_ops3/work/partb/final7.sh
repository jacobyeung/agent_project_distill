D=/project/community/jjyeung/okh7/b7e31d84a90c62f5/170235/ad2472b1be07d4193
cat $D/EXIT.json; echo; cat $D/JOB.log; echo; cat $D/RETURN_RECEIPT.json; echo
tar xzOf $D/result.tar.gz metadata/budget.json | head -c 1500; echo
tar tzf $D/result.tar.gz | awk -F/ '{print $1"/"$2}' | sort | uniq -c | head; tar tzf $D/result.tar.gz | grep -c PHASE_COMPLETE
tar xzOf $D/result.tar.gz native/probe/PROGRESS.jsonl | tail -3
ls /project/community/jjyeung/okh7/b7e31d84a90c62f5/ ; cat /project/community/jjyeung/okh7/b7e31d84a90c62f5/a.json 2>/dev/null | head -c 800
