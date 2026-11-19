# env P (package dir), TOK (token) ; job id from $P/a/8.txt
set -euo pipefail; umask 077; cd "$P"; JOB=$(cat "$P/a/8.txt"); [[ "$JOB" =~ ^[0-9]+$ ]]
RET=$TOK$(printf '%08x' $JOB)
test -e "$P/a/f" || /usr/bin/python3 -I -s -B "$P/a/7.py" --package "$P" --return-token "$RET" --out "$P/a/f"
ls -la $P/a/f; head -c 700 $P/a/f/EXIT.json; echo; sha256sum $P/a/f/*; for f in $P/a/x*; do echo "== $f"; head -3 $f; tail -5 $f; done
