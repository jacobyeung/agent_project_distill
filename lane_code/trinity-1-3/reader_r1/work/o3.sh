set -euo pipefail
umask 077
D=/project/community/jjyeung/okh7/5c1e9a07
P=/project/community/jjyeung/e47d0593fefec
printf '%s  %s\n' 1a60c9826f8d3d49081930e12dcf5434a3a876af805c2570585c7c29d4b98c03 "$D/1.tgz" | sha256sum -c -
test ! -e "$P"
mkdir -m 700 "$P"
tar -xzf "$D/1.tgz" -C "$P"
chmod 700 "$P/a"
cd "$P"
ls -la . a
CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 05:00:00
cat 2.json
TZ=UTC squeue -u $USER -o '%i %j %P %T %M %l %R'
