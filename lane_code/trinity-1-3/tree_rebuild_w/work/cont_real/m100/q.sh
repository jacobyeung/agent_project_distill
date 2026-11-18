R=/project/community/jjyeung/okh7/x_69d2930d/runs/673bc60f
echo "== ls run"; ls -la $R | head -40
echo "== ls m100"; ls -la $R/m100 | head -30
for f in $R/m100/artifact.json $R/m100/full_weights.json $R/binding.json $R/config.json; do echo "== FILE $f"; [ -f $f ] && { sha256sum $f; wc -c < $f; }; done
echo "== complete"; ls -d $R/*/ 2>/dev/null | head -20; ls $R/checkpoints 2>/dev/null | head
