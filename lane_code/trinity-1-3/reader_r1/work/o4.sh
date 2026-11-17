set -euo pipefail
umask 077
D=/project/community/jjyeung/okh7/8e2d4b61
P=/project/community/jjyeung/e09e45fda45db
printf '%s  %s\n' eadaba88d737c4b384e3fe6908c0420a35d78c3be6037b8302d154c7109f6fc4 "$D/1.tgz" | sha256sum -c -
test ! -e "$P"
mkdir -m 700 "$P"
tar -xzf "$D/1.tgz" -C "$P"
chmod 700 "$P/a"
cd "$P"
CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 05:00:00 > /dev/null
python3 -c "import json;c=json.load(open('2.json'));print(c['passed'],c['plan'][:12],c['package'][:12],c['inputs'][:12],c['time'],c['argv'][-1])"
TZ=UTC squeue -u $USER -o '%i %j %P %T %M %l %R' | grep -v advanced || true
