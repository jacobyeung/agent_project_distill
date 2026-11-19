set -euo pipefail; umask 077
O=/project/community/jjyeung/okh7; D=$O/n_7d20fbdd
mkdir -m 700 $D; cd $D
echo ewogInE4LzRlY2E2ZGQ5LzgzMzRmNmZlX3AuYmluIjogImh0dHBzOi8vc3RvcmFnZS5nb29nbGVhcGlzLmNvbS91cGxvYWQvc3RvcmFnZS92MS9iL2NtdS1ncHVjbG91ZC1qanlldW5nL28/dXBsb2FkVHlwZT1yZXN1bWFibGUmbmFtZT1xOCUyRjRlY2E2ZGQ5JTJGODMzNGY2ZmVfcC5iaW4maWZHZW5lcmF0aW9uTWF0Y2g9MCZ1cGxvYWRfaWQ9QUZ5M3NnMF9VYzNGNE1OV04xRXdWaGo1MUwyOUI5aUo4RzNwbTNiNjhERWNqY2g1MWxvc2ZTaVk3eXR2NU55OWJqOWFPV2dpdlZGNlRmREg4YU1mMkNkZjlaN01SX2RiUl9pTEc4ZnJlYUtQbFEiCn0K | base64 -d > sess.json; chmod 600 sess.json
echo "8efc84800b1704d5c3686a713f2f8185376c3759f1973bbab2abc36a050000b5  sess.json" | sha256sum -c --quiet && echo SESS_OK
head -c 1024 /dev/urandom > p.bin; echo "local md5 $(md5sum p.bin | cut -c1-32) sha256 $(sha256sum p.bin | cut -c1-64)"
timeout 120 python3 -B $O/x_ee227714/b/gcsput.py put sess.json q8/4eca6dd9/8334f6fe_p.bin p.bin 2>&1 | grep -v -i "https://" | tail -3; echo "gcsput rc=${PIPESTATUS[0]}"
cat sess.json.receipts.jsonl; ls -la $D
