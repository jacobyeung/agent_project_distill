set -euo pipefail
D=/project/community/jjyeung/okh7/6b960af0; P=/project/community/jjyeung/bf94a7976a7e9
test ! -e "$P"
mkdir -m 700 "$P"
install -m 600 "$D/p/"{0.tgz,0.json,3.py,BATCH.sh,CONFIG.json,SUBMIT.cmd,PACKAGE.json,INPUTS.example.json} "$P/"
mkdir -m 700 "$P/a" "$P/a/e"
install -m 600 "$D/i/4.py" "$P/a/4.py"; install -m 600 "$D/i/5.py" "$P/a/5.py"; install -m 600 "$D/i/6.py" "$P/a/6.py"
cd "$P" && sha256sum 0.tgz a/4.py a/5.py a/6.py && ls -la "$P" "$P/a"
df -h /project/community/jjyeung | tail -1
