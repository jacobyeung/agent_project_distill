K=/project/community/jjyeung/okh7
date -u +%FT%TZ
TZ=UTC squeue -u jjyeung -h -o '%i %j %P %T %r %S' 
echo "== all general"; TZ=UTC squeue -p general -h -o '%i %u %j %T %r' | head -20
echo "== advanced"; TZ=UTC squeue -p advanced -h -o '%i %u %j %T %r' | head -20
ls -la $K/x_69d2930d/runs/673bc60f/ $K/x_69d2930d/runs/673bc60f/m200 2>&1 | head -20
ls -la $K/x_69d2930d/o/ | grep 673bc60f | head
sha256sum $K/x_69d2930d/runs/673bc60f/m200/artifact.json
ls -la $K/ | head -50
du -sm $K/ae71c903 2>&1; ls -la $K/ae71c903 | head
ls -la $K/ae71c903_fetched | head -30
