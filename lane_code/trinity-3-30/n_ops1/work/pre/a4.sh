X=/project/community/jjyeung/okh7/x_22c714e1
for f in j.json p.json; do echo "==== $f"; python3 -B -c "import json,base64,sys;v=json.load(open(sys.argv[1]));print(base64.b64decode(v['payload']).decode())" $X/n/k/$f | gzip -c | base64 -w0; echo; done
