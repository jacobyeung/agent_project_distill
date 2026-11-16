D=/project/community/jjyeung/okh7/b7e31d84a90c62f5/170235/c75955208369b4e48
cat $D/EXIT.json; echo; cat $D/JOB.log; echo; cat $D/RETURN_RECEIPT.json; echo
tar tzf $D/result.tar.gz | head -40
echo ---CANARY; tar xzOf $D/result.tar.gz metadata/CANARY.json | head -c 6000
