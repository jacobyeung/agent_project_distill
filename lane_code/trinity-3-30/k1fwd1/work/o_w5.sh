D=/project/community/jjyeung/okh7/a15_cot_ap90eaf12c47ba5/944b6b6a8f8d8c7f
TZ=UTC sacct -j 173343 -X -n --format=State,Elapsed,ExitCode; ls -la $D/173343/ $D/173343/*/ 2>/dev/null | grep -v "^total" | head -20; cat $D/a.json 2>/dev/null
