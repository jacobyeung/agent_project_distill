set +e
export TZ=UTC
O=/home/jjyeung/okit; C=/project/community/jjyeung
echo "== C top"; ls -la $C | head -160
echo "== e193c2a3c"; ls -la $O/evalx_results/e193c2a3c $O/evalx_results/e3da9a577 $O/evalx_results/ebe307cf4
echo "== q8"; ls -la $C/q8 2>&1 | head; ls -la $C/q8/8865619b 2>&1 | head -30
echo "== okit i tmp cr"; ls -la $O/i $O/i/* $O/tmp $O/cr 2>&1 | head -80
