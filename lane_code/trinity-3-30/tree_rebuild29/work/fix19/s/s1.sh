R=/project/community/jjyeung/okh7/x_ee227714
ls $R | head -40
echo ---runs; ls $R/runs | head
echo ---run; ls -la $R/runs/6ed2c7aa | head -50
echo ---o; ls -la $R/o/172660 | head -30
echo ---live; ls -la $R/live 2>&1 | head -30
