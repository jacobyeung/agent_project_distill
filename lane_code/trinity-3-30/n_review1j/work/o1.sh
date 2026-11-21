X=/project/community/jjyeung/okh7/x_22c714e1; TZ=UTC date +%TZ >&2
cd $X/o/174134 < /dev/null && ls -la . >&2; ls -la live >&2 2>&1; cd $X/n && ls -R . | head -80 >&2
cd $X/o/174134 && tar czf - a0m.json a0r.json a3r.json receipt.json materialization.json q0.json tb.txt HOLD.txt 2>/dev/null
